# AGENTS.md — Domestic Gc Analyst

Context for any AI agent (Antigravity, Claude, etc.) working in this repo.
The project was handed over by its first developer; nobody else can answer questions
about it, so this file and `STATUS.md` are the source of truth. **Keep both up to date
whenever you change something.**

## What this is

A grocery analytics dashboard for a household. People photograph their shop bills and
send them to a Telegram bot; the numbers end up on a web dashboard showing spend, price
changes ("inflation") and how much of each item is bought over time.

The people who *use* the dashboard are not technical. They must never need to install
anything, create accounts or touch settings. All technical work (Supabase, Make.com,
Streamlit, GitHub) belongs to the owner.

## Architecture

```
Telegram bot ──► Make.com scenario ──► Supabase (Postgres) ──► Streamlit app (this repo)
 (photo of bill)   Gemini reads the       receipts + line_items     app.py, hosted on
                   photo → JSON           tables                    Streamlit Community Cloud
```

- **Telegram bot / Make.com / Supabase** all belong to the owner's accounts.
  Nothing about them lives in this repo except the SQL files in `sql/`.
- **App:** a single file, `app.py` (Python, Streamlit, pandas, Plotly, thefuzz,
  supabase-py). Hosted on Streamlit Community Cloud from this repo's `main` branch.
  **Every push to `main` redeploys the live app within about a minute.**

## Database (Supabase)

`receipts` (one row per bill)
| column | type | notes |
|---|---|---|
| receipt_id | uuid PK | |
| store_name | text | spelling varies ("RJ SUPER MARKET" vs "R J SUPER MARKET") |
| purchase_date | date | read by Gemini; can be wrong (e.g. year misread as 2020) |
| total_amount | numeric | total printed on the bill |
| created_at | timestamptz | |
| telegram_user_id | bigint, nullable | **added by `sql/001_people.sql`**; who sent the bill |

`line_items` (one row per line on a bill)
| column | type | notes |
|---|---|---|
| item_id | uuid PK | |
| receipt_id | uuid FK → receipts | |
| item_name | text | raw OCR text, inconsistent spelling/case |
| unit_price | numeric | |
| category | text | assigned by Gemini; inconsistent across bills |

There is **no quantity column**. The app assumes `quantity = 1` and
`item_total_amount = unit_price × 1`. If quantity is ever added in Make.com/Supabase,
`load_data()` already uses a real `quantity` column when present.

`dashboard_users` (only after `sql/001_people.sql`) — who may open the dashboard:
`id, display_name, access_code (unique), telegram_user_id (unique, nullable), is_admin`.

### Row Level Security
RLS is on. The app connects with the project's **anon key**, which exists only in
Streamlit's server-side secrets (never in the browser, never in git). Policies:
- `receipts`, `line_items`: anon may SELECT (see `sql/000_read_policies.sql`, already applied).
- `dashboard_users`: anon may SELECT/INSERT/UPDATE/DELETE (the app's People tab manages it).

**Gotcha:** if a table has RLS on but no SELECT policy, Supabase returns an *empty list*,
not an error. "Dashboard shows no receipts" usually means a missing policy.

## The app (`app.py`)

Layout, top to bottom: page config and design tokens → CSS (`inject_css`) → data layer
(`get_client`, `_fetch_all` pages through PostgREST's 1000-row limit, `load_data`) →
cleaning → charts → UI.

### Data cleaning (in `load_data` and friends). Keep these rules.
1. Drop lines with `unit_price <= 0` or a blank name (e.g. a ₹0 fridge on a Whirlpool invoice).
2. **Store names:** lowercase, strip non-alphanumerics → group key; show the most
   common spelling. Merges "RJ SUPER MARKET" and "R J SUPER MARKET".
3. **Duplicate receipts** (people resend the same bill; OCR misreads dates).
   Only compared *within the same sender* (`telegram_user_id`, NULL counts as one sender):
   - Rule 1: same store + same total + same set of (item name, rounded price) lines →
     keep the copy with the latest date. Catches a resend with a misread year.
   - Rule 2: same store + same date + same non-zero total → keep one. Catches resends
     where Gemini spelled an item differently ("Izzat papad" / "Iizzat papad").
4. **Fuzzy item names** (`build_name_map`): `thefuzz.fuzz.token_sort_ratio > 85` merges
   names into a `standard_item_name`. Greedy, most-purchased spelling first; label is
   prettified (`_pretty`: "NILKAMAL SATOO 250GM" → "Nilkamal Satoo 250gm").
   **All filtering and aggregation uses `standard_item_name`, never `item_name`.**
5. **One category per standard item:** the most common category Gemini gave it.

Both `load_data` and `build_name_map` are cached for 5 minutes (`@st.cache_data(ttl=300)`).
New receipts appear after ≤5 min or after pressing "↻ Refresh" (pressing `c` in the app
also clears the cache).

### Two versions of the app
- **`main` (live now):** single view. Sidebar picks an item; KPI cards (latest price,
  first price, total units, % inflation); price-over-time line chart; consumption bar
  chart with Weekly/Monthly toggle; purchase history table. Access is controlled only by
  Streamlit Cloud's private-app email invites. No per-person data.
- **`next/app_personal_links.py` (finished, not live):** the "user-centred" version.
  To ship it, it replaces `app.py` (see `STATUS.md`).
  - Everyone gets a **personal link** `https://<app>/?u=<access_code>`. Opening it shows
    *their* receipts only (matched by `receipts.telegram_user_id`). No accounts, no passwords.
  - Tabs: **Overview** (total spend, receipts, average basket, this month vs last;
    spend over time, by category, by store, top items, most-bought items, price-change
    table), **Items** (the old single-item view), **Receipts** (list + lines of one
    receipt), **People** (admins only: add a person, link them to a Telegram sender,
    copy/regenerate/remove their link).
  - Admins get a "Showing" selector: Everyone / each person / unlinked senders /
    old receipts with no sender.
  - Wrong or missing link → a friendly "paste your code" screen, no data.
  - Needs `sql/001_people.sql` first, otherwise it shows "Setup isn't finished".
  - How to ship it: see `STATUS.md`.

## Config and secrets

`.streamlit/config.toml` (committed):
- `[server] headless = true` is **required**. With `false`, Streamlit asks for an email
  address on startup; Streamlit Cloud can't answer, the health check fails and the app
  never starts ("Oh no. Error running app").
- Theme colours match the CSS tokens at the top of `app.py`.

`.streamlit/secrets.toml` (**never committed**; `.gitignore` covers it). See
`secrets.example.toml`. On Streamlit Cloud the same content goes in
App settings → Secrets.
```toml
[supabase]
url = "https://<project-ref>.supabase.co"
key = "<anon public key>"

[app]                      # optional, personal-links version only
public_url = "https://domestic-gc-analyst.streamlit.app"   # used to build personal links
```

## Running it

Local (Windows, Python 3.12):
```
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
Then open http://localhost:8501 (headless mode doesn't open the browser). For the
personal-links version, open `http://localhost:8501/?u=<your access_code>`.

Streamlit Cloud: Python 3.12, main file `app.py`, branch `main`. Streamlit needs
permission to read private repos on the GitHub account (Workspace settings →
Linked accounts → Private access).

## Known data problems (fix at the source when possible)
- The same bill was saved several times (one 12 Aug 2026 bill six times, once with the
  year read as 2020; a 5 Oct bill twice). The app hides these, but the real fix is in
  Make.com: before inserting, search `receipts` for the same store + date + total and skip.
- Gemini assigns different categories to the same item on different bills.
- At least one receipt has no line items (the app ignores it).
- Existing receipts have no `telegram_user_id`; after `001_people.sql` they show as
  "Old receipts (no sender)" until assigned (one `update`, see `STATUS.md`).

## Rules for agents working here
1. Never commit secrets. Keys go in `.streamlit/secrets.toml` locally and in Streamlit
   Cloud's Secrets box.
2. Database changes go in a new numbered file in `sql/` (`002_...sql`) and get noted in
   `STATUS.md`. Don't make untracked changes in the Supabase dashboard.
3. `main` is production. Test locally (`streamlit run app.py`) before pushing to `main`.
4. Keep the dashboard plain-language and layman-friendly: no jargon, no setup steps
   for users.
5. Use `width="stretch"`, not the deprecated `use_container_width`.
6. Inside `st.tabs`, use `return` from the render function rather than `st.stop()`
   (stop also stops later tabs from rendering).
7. Update `STATUS.md` (and this file, if architecture or rules change) in the same commit.
