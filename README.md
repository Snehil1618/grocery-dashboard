# Domestic Gc Analyst (Grocery Dashboard)

Grocery analytics dashboard for household expenses: Telegram bill photos → Make.com + Gemini → Supabase → Streamlit.

- **Live App:** https://grocery-dash.streamlit.app
- **Architecture & Agent Rules:** [`AGENTS.md`](AGENTS.md)
- **Current Status & Backlog:** [`STATUS.md`](STATUS.md)
- **Setup & Deployment Guide:** [`SETUP.md`](SETUP.md)
- **Database Scripts:** [`sql/`](sql/)

> [!NOTE]
> This repository is public. All real receipt data, personal identifiers, access codes, and API credentials live in Supabase and Streamlit Cloud secrets and must never be committed to git.

## Features
- **Personal Links:** Each user opens `https://grocery-dash.streamlit.app/?u=<access_code>` to see their receipts and spending trends. No passwords or accounts required.
- **Spend & Item Analytics:** Overview of spend, category breakdown, store frequency, inflation tracking, price changes, and consumption trends over time.
- **Admin Management:** Admins can manage household members, assign Telegram senders, and regenerate access links directly from the People tab.

## Running Locally

1. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
2. Configure secrets:
   Copy `secrets.example.toml` to `.streamlit/secrets.toml` and provide your Supabase URL, publishable/anon key, and app URL. (This file is git-ignored).
3. Run the application:
   ```bash
   python -m streamlit run app.py
   ```
   Open `http://localhost:8501/?u=<your-access-code>`.
