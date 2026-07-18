"""Snapshot HDFC forex card rates: download PDF, email it, archive to Drive.

Runs in GitHub Actions twice daily. Auth is a single user OAuth refresh token
(no service account — those have 0 quota on consumer Gmail). One token does both
Gmail send and Drive upload.

Env vars required:
  GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN
  DRIVE_FOLDER_ID   - target Drive folder (owned by the consenting account)
  MAIL_TO           - comma-separated recipients
"""
import base64
import os
import sys
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from zoneinfo import ZoneInfo

import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

PDF_URL = (
    "https://www.hdfc.bank.in/content/dam/hdfcbankpws/in/en/personal-banking/"
    "discover-products/interest-rates/hdfc-bank-treasury-forex-card-rates.pdf"
)
SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/gmail.send",
]


def env(name):
    v = os.environ.get(name)
    if not v:
        sys.exit(f"missing env var: {name}")
    return v


def download_pdf(path):
    r = requests.get(PDF_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
    r.raise_for_status()
    ctype = r.headers.get("Content-Type", "")
    # HDFC serves an HTML error page (200 OK) when the asset is unavailable.
    if "application/pdf" not in ctype or len(r.content) < 5000:
        sys.exit(f"unexpected response: type={ctype!r} bytes={len(r.content)}")
    with open(path, "wb") as f:
        f.write(r.content)
    return len(r.content)


def credentials():
    return Credentials(
        token=None,
        refresh_token=env("GOOGLE_REFRESH_TOKEN"),
        client_id=env("GOOGLE_CLIENT_ID"),
        client_secret=env("GOOGLE_CLIENT_SECRET"),
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )


def send_email(creds, path, label):
    recipients = [a.strip() for a in env("MAIL_TO").split(",") if a.strip()]
    msg = MIMEMultipart()
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = f"HDFC Forex Card Rates — {label} IST"
    msg.attach(MIMEText(
        f"Attached: HDFC Treasury Forex Card rates snapshot ({label} IST).\n"
        f"Source: {PDF_URL}\n", "plain"))
    with open(path, "rb") as f:
        part = MIMEApplication(f.read(), _subtype="pdf")
    part.add_header("Content-Disposition", "attachment",
                    filename=os.path.basename(path))
    msg.attach(part)
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    build("gmail", "v1", credentials=creds).users().messages().send(
        userId="me", body={"raw": raw}).execute()


def upload_drive(creds, path):
    media = MediaFileUpload(path, mimetype="application/pdf")
    build("drive", "v3", credentials=creds).files().create(
        body={"name": os.path.basename(path), "parents": [env("DRIVE_FOLDER_ID")]},
        media_body=media, fields="id").execute()


def main():
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    label = now.strftime("%Y-%m-%d %H:%M")
    os.makedirs("rates", exist_ok=True)
    path = os.path.join("rates", now.strftime("%Y-%m-%d_%H%M.pdf"))

    size = download_pdf(path)
    print(f"downloaded {size} bytes -> {path}")

    creds = credentials()
    send_email(creds, path, label)
    print("email sent")
    upload_drive(creds, path)
    print("uploaded to Drive")


if __name__ == "__main__":
    main()
