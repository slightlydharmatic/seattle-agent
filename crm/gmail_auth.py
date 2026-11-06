"""One-time Gmail sign-in. Run on your Mac:

    python -m crm.gmail_auth path/to/client_secret.json

A browser window opens; sign in to the inbox clients email and allow read-only
access. It prints one line of JSON: paste it as GMAIL_TOKEN_JSON in .env,
in Streamlit secrets, and in GitHub Actions secrets. Treat it like a password.
"""
import sys

from google_auth_oauthlib.flow import InstalledAppFlow

from crm.gmail_sync import SCOPES

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python -m crm.gmail_auth path/to/client_secret.json")
    creds = InstalledAppFlow.from_client_secrets_file(sys.argv[1], SCOPES).run_local_server(port=0)
    print(creds.to_json())
