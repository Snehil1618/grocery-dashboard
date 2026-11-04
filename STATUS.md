# STATUS — Domestic Gc Analyst (Grocery Dashboard)

_Last updated: 5 Nov 2026._

## Live Now
- **App URL:** https://grocery-dash.streamlit.app (deployed from `main` on Snehil's Streamlit account).
- **Repository:** https://github.com/Snehil1618/grocery-dashboard (public repository; no secrets or personal data committed).
- **Personal-Links & Roles:**
  - **Admins:** See all 4 tabs (**Overview**, **Items**, **Receipts**, and **People**), can view by individual sender or household total, and can manage links.
  - **Family Members:** See clean 2 tabs (**Overview** and **Items**) with combined household numbers. Raw receipts and admin management are completely hidden.
- **Bill Senders:** Snehil is currently the sole person sending bill photos to the Telegram bot, so all receipts belong to Snehil.
- **Database & Secrets:** `sql/000_read_policies.sql` and `sql/001_people.sql` applied in Supabase. Streamlit Cloud secrets configured with Supabase publishable key and `public_url`.

## Handover Checklist (Owner)
- [x] Accept the GitHub repository transfer.
- [x] Deploy the app from your Streamlit Cloud account at https://grocery-dash.streamlit.app.
- [x] Configure Supabase API keys (Streamlit Cloud configured with new publishable key).
- [x] Change any Supabase / Make.com / Telegram passwords the previous developer knew.
- [x] Run `sql/001_people.sql` and verify admin access.
- [x] Ship personal-links version (`app.py`) to `main` and clean up `next/`.
- [x] Configure family member view (household totals in Overview/Items, hide Receipts/People).

## Ideas & Backlog
1. **Retire the legacy Supabase JWT keys:**
   - Create a new Supabase secret key.
   - Update the Make.com scenario with the new key.
   - Test by sending one bill photo via Telegram and confirming it saves.
   - Disable/retire the legacy Supabase JWT keys in Supabase Project Settings.
2. **Stop duplicate bills at the source in Make.com:**
   - Before inserting into `receipts`, search Supabase for matching `store_name` + `purchase_date` + `total_amount` to prevent duplicates caused by repeated photo uploads.
3. **Item quantities from Gemini:**
   - Update Make.com prompt to ask Gemini for line-item quantities; write to a `quantity` column (supported by `load_data()`).
4. **Standardized category list:**
   - Provide a fixed category enumeration in the Gemini prompt so item categorization remains consistent across receipts.

## Change Log
- 2026-10-24: First version built and deployed; data cleaning (duplicates, store names, fuzzy names, categories); headless fix for Streamlit Cloud.
- 2026-10-25: Personal-links version written (`next/app_personal_links.py`).
- 2026-11-01: Handover complete. Repository transferred to Snehil (`Snehil1618/grocery-dashboard`). Deployed to `https://grocery-dash.streamlit.app`. Personal-links version promoted to production `app.py`; `next/` deleted. Supabase publishable key and public URL configured. Backlog updated.
- 2026-11-05: Family member read-only view shipped: non-admin links now see combined household grocery analytics across Overview and Items tabs; Receipts and People tabs remain admin-only.
