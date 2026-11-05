# STATUS — Domestic Gc Analyst (Grocery Dashboard)

_Last updated: 6 Nov 2026._

## Live Now
- **App URL:** https://grocery-dash.streamlit.app (deployed from `main` on Snehil's Streamlit account).
- **Repository:** https://github.com/Snehil1618/grocery-dashboard (public repository; no secrets or personal data committed).
- **Personal-Links & Roles:**
  - **Admins (5 Tabs):**
    1. **Overview:** Total spend, customizable monthly budget pacing tracker with velocity projections, grocery inflation index, spend over time, category distributions (with emojis), top items, and price mover breakdown.
    2. **Items:** Deep single-item explorer with OCR variant auditing and consumption trends.
    3. **Stores:** Head-to-head store price comparison ("Who is Cheaper?"), store price differentials, and savings potential across common items.
    4. **Receipts:** Interactive receipt browser, line-item inspector, and **1-Click CSV Data Export**.
    5. **People:** Household member link generator and Telegram sender linking.
  - **Family Members (2 Tabs):** Clean **Overview** and **Items** tabs with combined household grocery numbers and budget pacing. Raw receipts, store intelligence, and admin controls are hidden.
- **Bill Senders:** Snehil is currently the sole person sending bill photos to the Telegram bot, so all receipts belong to Snehil.
- **Receipt Types:** Gemini OCR processes printed supermarket bills, digital invoices, and clean, legible handwritten receipts and shop slips sent to the Telegram bot.
- **Database & Secrets:** `sql/000_read_policies.sql` and `sql/001_people.sql` applied in Supabase. Streamlit Cloud secrets configured with Supabase publishable key and `public_url`.

## Handover & Feature Checklist (Owner)
- [x] Accept GitHub repository transfer & deploy to Streamlit Cloud.
- [x] Configure Supabase API keys (new publishable key).
- [x] Change Supabase / Make.com / Telegram passwords.
- [x] Run `sql/001_people.sql` and verify admin access.
- [x] Ship personal-links version (`app.py`) to `main` and clean up `next/`.
- [x] Configure family member view (household totals in Overview/Items, hide Receipts/People).
- [x] Customizable monthly budget pacing widget with daily velocity & month-end projection.
- [x] Overall household grocery inflation index.
- [x] Store price comparison ("Who is Cheaper?") tab for admins.
- [x] 1-Click clean CSV data export in Receipts tab.

## Ideas & Backlog
1. **Retire the legacy Supabase JWT keys (Deferred):**
   - Create a new Supabase secret key, update Make.com, test one bill, and disable legacy JWT keys. (Low urgency; trusted developer).
2. **Item quantities from Gemini:**
   - Update Make.com prompt to ask Gemini for line-item quantities; write to a `quantity` column (supported by `load_data()`).
3. **Standardized category list:**
   - Provide a fixed category enumeration in the Gemini prompt so item categorization remains consistent across receipts.

## Change Log
- 2026-10-24: First version built and deployed; data cleaning; headless fix for Streamlit Cloud.
- 2026-10-25: Personal-links version written (`next/app_personal_links.py`).
- 2026-11-01: Handover complete. Repository transferred to Snehil (`Snehil1618/grocery-dashboard`). Deployed to `https://grocery-dash.streamlit.app`. Personal-links version promoted to production `app.py`; `next/` deleted. Supabase publishable key and public URL configured.
- 2026-11-05: Family member read-only view shipped: non-admin links now see combined household grocery analytics across Overview and Items tabs; Receipts and People tabs remain admin-only.
- 2026-11-06: Added full analyst feature suite (Store Price Comparison tab, customizable Monthly Budget Pacing widget, Household Inflation Index, and 1-Click CSV Export). Documented handwritten receipt support.
