# Dadtrial — daily HDFC forex rate snapshot

Twice a day (10:00 & 14:00 IST) a GitHub Actions cron job downloads HDFC's
Treasury Forex Card rates PDF, **emails it** to the recipients, **archives it**
to a Google Drive folder, and **commits a copy** to `rates/` here as a permanent
backup. HDFC overwrites its live PDF in place, so this is the only history.

One user OAuth refresh token does both the Gmail send and the Drive upload — no
service account (those have 0 storage quota on consumer Gmail).

## One-time setup

1. **Google Cloud Console** → new project → enable **Gmail API** and **Google
   Drive API**.
2. **OAuth consent screen** → set publishing status to **"In production"**.
   > Critical: in "Testing" mode Google expires refresh tokens after 7 days and
   > the job dies silently every week. "In production" tokens don't expire.
   > Click past the "unverified app" warning — fine for personal use.
3. **Credentials → Create OAuth client ID → Desktop app** → download the JSON as
   `client_secret.json` into this folder.
4. Mint the refresh token (local, once):
   ```bash
   pip install google-auth-oauthlib
   python get_refresh_token.py
   ```
   Consent as **your** account. Copy the printed `REFRESH_TOKEN` (and the
   client id/secret).
5. Create a folder in your Drive (e.g. "HDFC Rates"). Its ID is the last part of
   the URL: `drive.google.com/drive/folders/<THIS_IS_THE_ID>`.
6. **Repo → Settings → Secrets and variables → Actions** → add:

   | Secret | Value |
   |---|---|
   | `GOOGLE_CLIENT_ID` | from step 4 |
   | `GOOGLE_CLIENT_SECRET` | from step 4 |
   | `GOOGLE_REFRESH_TOKEN` | from step 4 |
   | `DRIVE_FOLDER_ID` | from step 5 |
   | `MAIL_TO` | `` |

## Test it

Actions tab → **HDFC forex rates snapshot** → **Run workflow**. Then check:
both inboxes got the email, the PDF is in the Drive folder, and a new file
appeared under `rates/`.

## Files

- `send_rates.py` — the job (download → email → Drive upload).
- `.github/workflows/rates.yml` — schedule + commit.
- `get_refresh_token.py` — one-time token helper (not run by CI).
