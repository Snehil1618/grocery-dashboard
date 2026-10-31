# Domestic Gc Analyst

Grocery analytics dashboard: Telegram bill photos → Make.com + Gemini → Supabase → Streamlit.

- **Taking over / setting up:** read [`SETUP.md`](SETUP.md).
- **What's done and what's next:** [`STATUS.md`](STATUS.md).
- **How it all works (for developers and AI agents):** [`AGENTS.md`](AGENTS.md).
- **Database scripts:** [`sql/`](sql/).

Run locally:
```
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
Needs `.streamlit/secrets.toml` (copy `secrets.example.toml`). Never commit it.
