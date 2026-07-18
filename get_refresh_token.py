"""One-time local helper: mint a Google OAuth refresh token.

Run ONCE on your own machine (not in CI). It opens a browser, you consent as the
account whose Drive/Gmail should be used, and it prints a refresh token to paste
into the GitHub secret GOOGLE_REFRESH_TOKEN.

    pip install google-auth-oauthlib
    python get_refresh_token.py        # needs client_secret.json in this dir
"""
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/gmail.send",
]

if __name__ == "__main__":
    flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
    print("\nCLIENT_ID:    ", creds.client_id)
    print("CLIENT_SECRET:", creds.client_secret)
    print("REFRESH_TOKEN:", creds.refresh_token)
    if not creds.refresh_token:
        print("\nNo refresh token returned — revoke the app's access at "
              "https://myaccount.google.com/permissions and re-run.")
