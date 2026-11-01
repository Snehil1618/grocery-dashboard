# AGENTS.md — Domestic Gc Analyst (Grocery Dashboard)

Context for any AI agent (Antigravity, Claude, etc.) working in this repo.
The project was handed over to Snehil and is live at https://grocery-dash.streamlit.app.
This file and `STATUS.md` are the source of truth. **Keep both up to date whenever you change something.**

## What this is

A grocery analytics dashboard for a household. People photograph their shop bills and send them to a Telegram bot; the numbers end up on a web dashboard showing spend, price changes ("inflation"), and how much of each item is bought over time.

The people who *use* the dashboard are not technical. They must never need to install anything, create accounts, or touch settings. All technical work (Supabase, Make.com, Streamlit, GitHub) belongs to the owner.

> [!IMPORTANT]
> **This repository is public.** Never commit any personal information, Telegram IDs, user access codes, receipt contents, or API credentials to git. Secrets belong exclusively in `.streamlit/secrets.toml` locally and Streamlit Cloud Secrets online.

## Architecture

```
Telegram bot ──► Make.com scenario ──► Supabase (Postgres) ──► Streamlit app (this repo)
 (photo of bill)   Gemini reads the       receipts + line_items     app.py, hosted on
                   photo → JSON           tables                    Streamlit Community Cloud
                                                                    (https://grocery-dash.streamlit.app)
```

- **Telegram bot / Make.com / Supabase:** Belong to the owner's accounts.
  Nothing about them lives in this repo except SQL files in `sql/`.
- **App:** Single file, `app.py` (Python, Streamlit, pandas, Plotly, thefuzz, supabase-py).
  Hosted on Streamlit Community Cloud from this repo's `main` branch.
  **Every push to `main` redeploys the live app within about a minute.**
- **Current Sender Status:** The owner (Snehil) is currently the only person sending bills to the Telegram bot, so all receipts belong to Snehil.

## Database (Supabase)

`receipts` (one row per bill)
| column | type | notes |
|---|---|---|
| receipt_id | uuid PK | |
| store_name | text | spelling varies ("RJ SUPER MARKET" vs "R J SUPER MARKET") |
| purchase_date | date | read by Gemini; can be wrong (e.g. year misread as 2020) |
| total_amount | numeric | total printed on the bill |
| created_at | timestamptz | |
| telegram_user_id | bigint, nullable | Added by `sql/001_people.sql`; identifies who sent the bill |

`line_items` (one row per line on a bill)
| column | type | notes |
|---|---|---|
| item_id | uuid PK | |
| receipt_id | uuid FK → receipts | |
| item_name | text | raw OCR text, inconsistent spelling/case |
| unit_price | numeric | |
| category | text | assigned by Gemini; inconsistent across bills |

There is **no quantity column**. The app assumes `quantity = 1` and `item_total_amount = unit_price × 1`. If quantity is ever added in Make.com/Supabase, `load_data()` already uses a real `quantity` column when present.

`dashboard_users` (created by `sql/001_people.sql`) — who may open the dashboard:
`id, display_name, access_code (unique), telegram_user_id (unique, nullable), is_admin`.

### Row Level Security & Keys
RLS is enabled.
- The app connects to Supabase using the project's **publishable key** in Streamlit's server-side secrets (never in client-side code, never in git).
- Policies:
  - `receipts`, `line_items`: anon/publishable may SELECT (`sql/000_read_policies.sql`, applied).
  - `dashboard_users`: anon/publishable may SELECT/INSERT/UPDATE/DELETE (`sql/001_people.sql`, applied; managed in the People tab).
- **Make.com keys:** Make.com currently connects using legacy Supabase JWT keys. Migrating Make.com to a new secret key and retiring the legacy keys is on the backlog.

## The App (`app.py`)

Layout, top to bottom: page config and design tokens → CSS (`inject_css`) → data layer (`get_client`, `_fetch_all` pages through PostgREST's 1000-row limit, `load_data`, `load_users`) → cleaning → user authentication (`current_profile`) → charts → UI.

### Navigation & Personal Links
The personal-links version is the production app:
- Users open a **personal link**: `https://grocery-dash.streamlit.app/?u=<access_code>`. Opening it filters the dashboard to show *their* receipts (matched by `receipts.telegram_user_id`). No logins or passwords needed.
- If no valid `?u=` code is provided, a friendly gate screen asks for their access code.
- **Tabs:**
  - **Overview:** Total spend, receipt count, average basket, this month vs last month, spend over time, category breakdown, store frequency, top items, and price-change table.
  - **Items:** Single-item view with price inflation metrics, price-over-time line chart, weekly/monthly consumption bar chart, and item purchase history.
  - **Receipts:** Interactive list of receipts and line items per bill.
  - **People (Admins only):** Add household members, link users to Telegram sender IDs, and copy, regenerate, or remove personal access links.
- Admins have a "Showing" selector in the sidebar: Everyone / each person / unlinked senders / old receipts with no sender.

### Data Cleaning Rules (in `load_data` and friends)
1. Drop lines with `unit_price <= 0` or a blank name.
2. **Store names:** lowercase, strip non-alphanumerics → group key; show the most common spelling (e.g., merges "RJ SUPER MARKET" and "R J SUPER MARKET").
3. **Duplicate receipts:** (resends / misread dates within the same `telegram_user_id`):
   - Rule 1: same store + same total + same set of (item name, rounded price) lines → keep copy with the latest date.
   - Rule 2: same store + same date + same non-zero total → keep one copy.
4. **Fuzzy item names** (`build_name_map`): `thefuzz.fuzz.token_sort_ratio > 85` merges variant names into a `standard_item_name`.
   - **All filtering and aggregation uses `standard_item_name`, never raw `item_name`.**
5. **One category per standard item:** assigned by the most frequent category Gemini gave it.

`load_data` and `build_name_map` are cached for 5 minutes (`@st.cache_data(ttl=300)`). Pressing "↻ Refresh" or key `c` clears the cache.

## Config and Secrets

`.streamlit/config.toml` (committed):
- `[server] headless = true` is required so Streamlit Cloud starts without prompting for an email address.
- Theme colors match the tokens at the top of `app.py`.

`.streamlit/secrets.toml` (**never committed**; covered by `.gitignore`):
```toml
[supabase]
url = "https://<project-ref>.supabase.co"
key = "<Supabase publishable key>"

[app]
public_url = "https://grocery-dash.streamlit.app"
```

## Running Locally

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
Open `http://localhost:8501/?u=<your_access_code>`.

## Rules for Agents Working Here
1. **Never commit secrets or personal data.** The repo is public. Keys go in `.streamlit/secrets.toml` locally and in Streamlit Cloud's Secrets.
2. Database schema changes go in a new numbered SQL file in `sql/` (e.g. `002_...sql`) and are recorded in `STATUS.md`.
3. `main` is production. Test locally before pushing to `main`.
4. Keep the dashboard plain-language and layman-friendly: no jargon or complicated setups for users.
5. Use `width="stretch"`, not deprecated `use_container_width`.
6. Inside `st.tabs`, use `return` from render functions rather than `st.stop()`.
7. Always update `STATUS.md` and `AGENTS.md` in the same commit whenever architectural state or roadmap items change.
