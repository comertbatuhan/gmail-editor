from __future__ import print_function
import os.path
import pandas as pd
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_gmail_service():
    """Authenticate & return a Gmail API service object."""
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("../config/credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("../config/token.json", "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def length_of_mail(service):
    """Calculate number of messages in the mailbox."""
    try:
        response = service.users().messages().list(userId="me").execute()
        messages = response.get("messages", [])
        print(f"Total messages in mailbox: {len(messages)}")
    except Exception as e:
        print(f"An error occurred: {e}")


def fetch_messages(service, max_count=1000, save_path="raw_emails.parquet"):
    """Fetch `max_count` messages from the Primary tab and save as json file."""
    query = "category:primary"
    all_data = []
    next_page_token = None
    fetched = 0

    while fetched < max_count:
        response = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=min(500, max_count - fetched),  # Gmail API limit per call
            pageToken=next_page_token
        ).execute()

        messages = response.get("messages", [])
        if not messages:
            break

        for msg_meta in messages:
            try:
                msg = service.users().messages().get(
                    userId="me",
                    id=msg_meta["id"],
                    format="metadata",
                    metadataHeaders=["Subject", "From", "Date"],
                ).execute()
                hdrs = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
                subject = hdrs.get("Subject", "").strip()
                sender = hdrs.get("From", "").strip()
                date = hdrs.get("Date", "").strip()

                all_data.append({
                    "id": msg_meta["id"],
                    "sender": sender,
                    "subject": subject,
                })
            except Exception as e:
                print(f"Error fetching message {msg_meta['id']}: {e}")

        fetched += len(messages)
        next_page_token = response.get("nextPageToken")
        print(f"Fetched {fetched} messages...")

        if not next_page_token:
            break

    # Save to json file
    df = pd.DataFrame(all_data)
    df['id'] = list(range(1,df['id'].shape[0]+1))
    result = df.to_dict(orient='records')
    with open("../data/raw_emails.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n Saved {len(df)} messages")
