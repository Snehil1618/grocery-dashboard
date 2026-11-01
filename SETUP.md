# Grocery Dashboard Setup & Deployment Guide

This guide documents the setup, deployment, and ongoing maintenance for the grocery dashboard.

## Production Deployment (Streamlit Community Cloud)

The production dashboard is deployed at: **https://grocery-dash.streamlit.app**

### Configuration
1. **Repository:** `Snehil1618/grocery-dashboard` (Branch: `main`)
2. **Main file path:** `app.py`
3. **Python Version:** 3.12
4. **Secrets Configuration:**
   In Streamlit Cloud → App settings → Secrets:
   ```toml
   [supabase]
   url = "https://<your-project-ref>.supabase.co"
   key = "<your-supabase-publishable-key>"

   [app]
   public_url = "https://grocery-dash.streamlit.app"
   ```

> [!IMPORTANT]
> Because this repository is public, never commit real URLs with project IDs, API keys, or access codes to git.

---

## Local Development (Windows / Antigravity)

### 1. Prerequisites
- Python 3.12
- Git

### 2. Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/Snehil1618/grocery-dashboard.git
   cd grocery-dashboard
   ```
2. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
3. Set up local secrets:
   Create `.streamlit/secrets.toml` (copy from `secrets.example.toml`):
   ```toml
   [supabase]
   url = "https://<your-project-ref>.supabase.co"
   key = "<your-supabase-publishable-key>"

   [app]
   public_url = "https://grocery-dash.streamlit.app"
   ```
4. Run locally:
   ```bash
   python -m streamlit run app.py
   ```
   Open `http://localhost:8501/?u=<your-admin-access-code>`.

---

## Adding Household Members

1. Log in with your admin link: `https://grocery-dash.streamlit.app/?u=<admin_access_code>`
2. Go to the **People** tab.
3. Once a household member sends a bill to the Telegram bot, their Telegram ID appears under unlinked senders.
4. Add the person by name, link their Telegram sender ID, and share their generated link (`https://grocery-dash.streamlit.app/?u=...`).
5. Each person sees their own spend and bills automatically without needing passwords.
