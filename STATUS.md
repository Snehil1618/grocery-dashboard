# STATUS — Domestic Gc Analyst (Grocery Dashboard)

_Last updated: 1 Nov 2026._

## Live Now
- **App URL:** https://grocery-dash.streamlit.app (deployed from `main` on Snehil's Streamlit account).
- **Repository:** https://github.com/Snehil1618/grocery-dashboard (public repository; no secrets or personal data committed).
- **Personal-Links Version:** Shipped and running as `app.py`. Admin access code verified and working. The old `next/` folder has been removed.
- **Bill Senders:** Snehil is currently the sole person sending bill photos to the Telegram bot, so all receipts belong to Snehil.
- **Database & Secrets:** `sql/000_read_policies.sql` and `sql/001_people.sql` applied in Supabase. Streamlit Cloud secrets are configured with the new Supabase publishable key and `public_url`.

## Handover Checklist (Owner)
- [x] Accept the GitHub repository transfer.
- [x] Deploy the app from your Streamlit Cloud account at https://grocery-dash.streamlit.app.
- [x] Configure Supabase API keys (Streamlit Cloud configured with new publishable key).
- [x] Change any Supabase / Make.com / Telegram passwords the previous developer knew.
- [x] Run `sql/001_people.sql` and verify admin access.
- [x] Ship personal-links version (`app.py`) to `main` and clean up `next/`.

## Ideas & Backlog
1. **Retire the legacy Supabase JWT keys:**
   - Create a new Supabase secret key.
   - Update the Make.com scenario with the new key.
   - Test by sending one bill photo via Telegram and confirming it saves.
   - Disable/retire the legacy Supabase JWT keys in Supabase Project Settings.
2. **"View everything" option for family members:**
   - Allow household members to see combined/household-wide grocery spend and trends across all receipts.
   - Ensure the **People** tab remains strictly restricted to admins.
3. **Stop duplicate bills at the source in Make.com:**
   - Before inserting into `receipts`, search Supabase for matching `store_name` + `purchase_date` + `total_amount` to prevent duplicates caused by repeated photo uploads.
4. **Item quantities from Gemini:**
   - Update Make.com prompt to ask Gemini for line-item quantities; write to a `quantity` column (supported by `load_data()`).
5. **Standardized category list:**
   - Provide a fixed category enumeration in the Gemini prompt so item categorization remains consistent across receipts.
6. **Telegram bot response with personal link:**
   - Have the Telegram bot reply to the sender with their personal dashboard link (`https://grocery-dash.streamlit.app/?u=<access_code>`) after processing each receipt.

## Change Log
- 2026-10-24: First version built and deployed; data cleaning (duplicates, store names, fuzzy names, categories); headless fix for Streamlit Cloud.
- 2026-10-25: Personal-links version written (`next/app_personal_links.py`).
- 2026-11-01: Handover complete. Repository transferred to Snehil (`Snehil1618/grocery-dashboard`). Deployed to `https://grocery-dash.streamlit.app`. Personal-links version promoted to production `app.py`; `next/` deleted. Supabase publishable key and public URL configured. Backlog updated with key rotation, family view-all, and Make.com deduplication.
