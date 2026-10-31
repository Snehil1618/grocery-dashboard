# STATUS — Domestic Gc Analyst

_Last updated: 1 Nov 2026, at handover._

## Live now
- App: https://domestic-gc-analyst.streamlit.app, deployed from `main`.
- `main` has the single-item dashboard (see `AGENTS.md` → "Two versions").
- Supabase: `receipts` + `line_items` with anon read policies. Make.com scenario is
  saving bills from Telegram.

## Handover checklist (owner)
- [ ] Accept the GitHub repository transfer.
- [ ] Deploy the app from **your** Streamlit Cloud account (see `SETUP.md`), using the
      same address after the previous developer deletes theirs.
- [ ] **Rotate the Supabase API keys** (Project Settings → API) and put the new anon key in
      Streamlit's Secrets. The old key was used on the previous developer's machine.
- [ ] Change any Supabase / Make.com / Telegram passwords the previous developer knew.

## Next: ship the personal-links version (`next/app_personal_links.py`)
1. In Supabase → SQL Editor, run `sql/001_people.sql`. It returns your admin
   `access_code`; your link is `https://domestic-gc-analyst.streamlit.app/?u=<access_code>`.
   (Change `'Owner'` in the file to your name first, or rename yourself later.)
2. In Make.com, in the module that inserts into `receipts`, map the new
   `telegram_user_id` field to the Telegram trigger's **Message → From → ID**.
   Without this, nobody's receipts can be told apart.
3. Optional: give the existing receipts to yourself. Send one new bill to the bot, find
   your Telegram ID in the People tab (it appears as an "unlinked sender"), then run
   `update receipts set telegram_user_id = <your id> where telegram_user_id is null;`
4. Replace `app.py` with `next/app_personal_links.py` (copy its contents over `app.py`,
   delete the `next/` folder) and push to `main`. Streamlit redeploys in about a minute.
   Ask your AI agent to "ship next/app_personal_links.py as app.py".
5. Open your admin link. In **People**: link yourself to your Telegram sender, then add
   each family member after they've sent one bill, and send them their link.
6. Optional: in Streamlit (Share → "Make this app public") switch off email invites so a
   personal link is all anyone needs. Trade-off: anyone who has someone's link can see
   that person's receipts. Links can be regenerated from the People tab.

## Ideas / backlog
- Stop duplicate bills at the source in Make.com (search before insert).
- Ask Gemini for quantity per line and store it; the app will use it automatically.
- Fixed category list in the Gemini prompt so categories stay consistent.
- Have the Telegram bot reply with the person's dashboard link after each bill.

## Change log
- 2026-10-24: First version built and deployed; data cleaning (duplicates, store names,
  fuzzy names, categories); headless fix for Streamlit Cloud.
- 2026-10-25: Personal-links version written (`next/app_personal_links.py`).
- 2026-11-01: Handover kit added (`AGENTS.md`, `STATUS.md`, `SETUP.md`, `sql/`).
