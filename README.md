# AI Data Solutions Accelerator — Public Website

A simple website: a visitor types a business requirement + schema, clicks
Generate, and all 6 agents run automatically on the server. Only the final
result is shown — the API key stays hidden on the server the whole time.

## What you'll need
- A free GitHub account (github.com) — to store the code
- A free Render account (render.com) — to actually host/run the website
- Your OpenAI API key (rotated, never shared anywhere public)

This guide assumes you've never done this before — follow every step in order.

---

## Part 1: Put the code on GitHub

1. Go to **github.com**, sign in (or create a free account).
2. Click the **+** icon top-right → **New repository**.
3. Name it something like `ai-data-accelerator`. Leave it **Public** or **Private**, either works. Click **Create repository**.
4. On the new repo's page, click **uploading an existing file** (a link on the page).
5. Drag in every file and folder from this `website` folder — `app.py`, `requirements.txt`, `.gitignore`, and the `templates` and `prompts` folders (with their contents).
   - **Do NOT create or upload any file containing your API key.** It never goes in this repo.
6. Scroll down, click **Commit changes**.

Your code is now on GitHub.

---

## Part 2: Deploy it on Render

1. Go to **render.com**, sign up (you can sign up directly with your GitHub account — this makes the next step easier).
2. Click **New +** → **Web Service**.
3. Connect your GitHub account if asked, then select the `ai-data-accelerator` repo you just created.
4. Fill in these settings:
   - **Name**: anything you like (this becomes part of your URL)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free
5. Scroll to **Environment Variables** and add these two:
   | Key | Value |
   |---|---|
   | `OPENAI_API_KEY` | your rotated OpenAI key |
   | `SITE_ACCESS_CODE` | a password you make up, e.g. `hackathon2026` |

   Setting `SITE_ACCESS_CODE` means visitors need to type this code before the site will run any agents — this protects your API key from being used by random strangers who find the link. Share this code only with people you want using the site. If you skip this variable entirely, the site is open to anyone with the link.

6. Click **Create Web Service**.

Render will now build and start your site — this takes a few minutes the first time. When it's done, you'll see a URL like `https://ai-data-accelerator.onrender.com` at the top of the page. That's your live, public website.

---

## Part 3: Test it

1. Open the URL Render gave you.
2. If you set an access code, enter it.
3. Paste in a business requirement and a schema (see the examples in the code repo's `scenario1_ad_reporting_brownfield` folder if you want a ready-made test).
4. Click **Generate** and wait — it calls all 6 agents in sequence, so it can take a minute or so.
5. The final SQL + dashboard template should appear on the page.

## Important notes

- **Free tier hosting sleeps when unused.** Render's free tier spins the site down after periods of no traffic, so the first visit after a while may take 30-60 seconds to "wake up" — this is normal, not a bug.
- **Cost**: every click of "Generate" makes 6 real API calls. Monitor usage at platform.openai.com to avoid surprise charges, especially since this is public.
- **If you ever need to change the API key** (e.g., after rotating it again), go to your Render service → Environment → update `OPENAI_API_KEY` → it redeploys automatically.
- **This prompt set is unvalidated against OpenAI models** (see pipeline_openai's README for detail) — test the output quality on a known scenario before relying on or sharing this widely.
