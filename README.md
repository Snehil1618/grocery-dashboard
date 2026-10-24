# Domestic Gc Analyst

Personal grocery analytics dashboard: Telegram receipts → Make.com/Gemini → Supabase → Streamlit.

## Run locally
```
pip install -r requirements.txt
streamlit run app.py
```
Create `.streamlit/secrets.toml` (never commit it):
```toml
[supabase]
url = "https://<project>.supabase.co"
key = "<anon key>"
```

## Deploy (Streamlit Community Cloud)
Deploy this private repo at share.streamlit.io, paste the secrets above under
**Advanced settings → Secrets**, then use **Share** to invite viewers by email.
