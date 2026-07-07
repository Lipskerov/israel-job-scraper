# 🔍 Israel Job Scraper

A **3-channel job scraper for the Israeli market** — pulls listings from **AllJobs.co.il** (Israel's largest job board) *and* from the closed **Telegram** and **WhatsApp** job groups where a huge share of Israeli biotech/tech roles are actually posted first. Everything is auto-translated **Hebrew → English** and exported to **Excel / CSV / JSON**.

Built during a 6-month post-PhD job hunt, after I realized the best roles never hit the job boards — they circulate in messenger groups you have to be *in* at the right minute.

> ⚠️ **Personal-use tool.** It scrapes on *your own behalf*, using *your own* accounts (your Telegram login, your WhatsApp Web session). It ships **no credentials** — you add your own (see setup below). Respect each platform's Terms of Service and rate-limit responsibly.

---

## What it does

| Channel | How it works | Auth |
|---|---|---|
| 🏢 **AllJobs.co.il** | Scrapes the public board — 58 categories, 11 regions, 9 job types, free-text search, multi-page | none |
| 💬 **Telegram** | Reads posts from job **groups/channels you're already a member of**, via your own account (Telethon) | your API creds + phone (one-time code) |
| 📱 **WhatsApp** | Reads posts from your **WhatsApp groups**, via a `whatsapp-web.js` bridge | scan a QR code once |

All three: Hebrew → English translation (Google Translate via `deep-translator`), unified UI, per-channel export.

---

## Architecture

```
Streamlit app (app.py)  ── 3 tabs ──┐
                                     ├─ 🏢 alljobs_scraper.py     (requests + BeautifulSoup)
                                     ├─ 💬 telegram_scraper.py    (Telethon, your account)
                                     └─ 📱 whatsapp_scraper.py ──> whatsapp_server.js
                                                                   (Node bridge on localhost:8765,
                                                                    whatsapp-web.js + QR login)
```

---

## Build & install

**Prerequisites:** Python 3.9+, Node.js 18+ (for the WhatsApp channel only).

```bash
git clone https://github.com/<your-username>/israel-job-scraper.git
cd israel-job-scraper

# Python deps
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Node deps (only needed for the WhatsApp channel)
npm install
```

Then create your `.env` (see next section):

```bash
cp .env.example .env      # then fill in your own values
```

---

## Run

```bash
streamlit run app.py      # opens http://localhost:8501
```

You'll get three tabs. **AllJobs works immediately, no setup.** Telegram and WhatsApp need the one-time credential setup below.

### AllJobs also works headless (CLI)

```bash
python3 alljobs_scraper.py --list-categories
python3 alljobs_scraper.py --category 235 --pages 3 --output jobs.csv
python3 alljobs_scraper.py --search "python developer" --pages 2 --output jobs.json
```

(Category 235 ≈ Software. Run `--list-categories` / `--list-regions` / `--list-roles --category N` to explore filters. See `AllJobs_Scraper_Reference.md` for the full option list.)

---

## 🔑 Setting up YOUR credentials

**None of this ships with the repo.** `.env`, the Telegram session, and the WhatsApp session are all `.gitignore`d and stay on your machine only.

### 💬 Telegram — scrape job groups you're in

Telegram job channels (search `דרושים` / `jobs` + your field) often repost roles hours before the boards. To read them programmatically you authenticate as **yourself** (Telethon uses your normal account — it can only see groups *you've already joined*).

1. **Get your API credentials** → go to **https://my.telegram.org** → log in → **API development tools** → create an app. Copy the **`api_id`** and **`api_hash`**.
2. **Fill `.env`:**
   ```
   TELEGRAM_API_ID=1234567
   TELEGRAM_API_HASH=your_hash_here
   TELEGRAM_PHONE=+9725XXXXXXXX
   ```
3. **First run → verify.** On the first Telegram scrape, Telegram sends a **login code to your Telegram app**; enter it in the UI. A `telegram.session` file is created so you don't re-auth next time. *(This file is a live login token — it's gitignored and must never be shared.)*
4. **Pick groups & scrape.** The app lists every group/channel you're a member of (`list_dialogs()`); select the job ones and pull recent messages. Posts shorter than ~30 chars are filtered as noise; first line becomes the title, full text the description; everything is timestamped and translated.

> **To add more sources, just join more Telegram job groups in your normal Telegram app** — they'll appear in the picker on the next run. No code change needed.

### 📱 WhatsApp — scrape your job groups

Uses a small Node bridge (`whatsapp_server.js`, on `localhost:8765`) wrapping `whatsapp-web.js`. It logs in exactly like WhatsApp Web.

1. `npm install` (once).
2. Open the **WhatsApp** tab → click **Connect** → a **QR code** appears → scan it with your phone (WhatsApp → Linked Devices). The session is saved in `.wwebjs_auth/` (gitignored), so you only scan once.
3. The app lists your WhatsApp groups → pick the job ones → pull messages (`/messages?chat_id=…&limit=…`), translated + exported.

> **To add sources, join the relevant WhatsApp job groups on your phone** — they show up in the group picker automatically.

### 🤖 (Optional) AI structuring
`.env.example` includes an `ANTHROPIC_API_KEY` slot for optionally post-processing messy posts into clean fields. It's off by default; leave it blank if you don't need it.

---

## Export

Every channel exports to **Excel** (`telegram_jobs_*.xlsx`, `whatsapp_jobs_*.xlsx`); AllJobs also does CSV/JSON. All UTF-8, Hebrew-translated, Excel-safe.

---

## 🔒 Security

- **No credentials in this repo.** `.env`, `*.session`, `.wwebjs_auth/`, `.wwebjs_cache/` are all gitignored.
- Your Telegram session and WhatsApp session are **live login tokens** — treat them like passwords; never commit or share them.
- If you ever fork/push, run `git status` first and confirm none of the above are staged.

## ⚖️ Use responsibly

This tool automates reading content **your own accounts already have access to**. It's for personal job-searching. Don't use it to mass-harvest, spam, or violate AllJobs / Telegram / WhatsApp Terms of Service. Keep the built-in rate limits on.

## License

MIT — do what you want, no warranty. Attribution appreciated.
