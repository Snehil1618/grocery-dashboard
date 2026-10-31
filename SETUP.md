# Taking over the grocery dashboard: plain steps

You already own the Supabase database and the Make.com automation. These steps move the
**website** to your accounts too. Allow about 20 minutes.

## 1. Accept the code (GitHub)
You'll get an email from GitHub about a repository transfer for `grocery-dashboard`.
Open it and accept. The code now lives in your GitHub account.

## 2. Put the website on your Streamlit account
1. Go to https://share.streamlit.io and choose **Continue with GitHub** (your account).
2. Allow Streamlit to see **private repositories** when asked. If you skip it, Streamlit
   will say the repository "does not exist". You can turn it on later under
   Workspace settings → Linked accounts → Private access → Connect here.
3. Wait until the previous developer confirms they've deleted their copy of the app.
4. **Create app** → Deploy from GitHub:
   - Repository: `<your-username>/grocery-dashboard`
   - Branch: `main`
   - Main file path: `app.py`
   - App URL: `domestic-gc-analyst`
5. **Advanced settings:** Python **3.12**. In **Secrets**, paste:
   ```toml
   [supabase]
   url = "https://cbukojcgfwquykfnnwpu.supabase.co"
   key = "PASTE YOUR NEW ANON KEY HERE"
   ```
   (Your anon key is in Supabase → Project Settings → API. Do step 3 first so this is
   the new key.)
6. Click **Deploy**. It's ready in 2–3 minutes.
7. To let someone see it: open the app → **Share** → type their email → **Invite**.

## 3. Lock the old keys
In Supabase → Project Settings → API, rotate (regenerate) the keys, then paste the new
anon key into Streamlit → your app → Settings → Secrets. The old key was used on the
previous developer's computer.

## 4. Keep improving it with an AI agent (Antigravity)
1. Download the code: in Antigravity (or any Git tool), clone
   `https://github.com/<your-username>/grocery-dashboard`.
2. Open the folder in Antigravity. It automatically reads `AGENTS.md`, which explains
   the whole project to the agent.
3. To run it on your computer, create `.streamlit/secrets.toml` from
   `secrets.example.toml` with your Supabase URL and key, then ask the agent to
   "run the app locally".
4. Ask the agent to "read STATUS.md and help me ship the personal-links version".
   That's the next planned step: everyone gets their own private link and only sees
   their own bills.
