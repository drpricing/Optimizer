import os
import json
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials

def authenticate_drive():
    # Load Google service account JSON from GitHub Secrets
    service_account_info = json.loads(os.environ["GDRIVE_SERVICE_ACCOUNT_JSON"])

    # Define scope for Google Drive access
    scope = ["https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)

    # Authenticate with PyDrive2
    gauth = GoogleAuth()
    gauth.credentials = credentials
    return GoogleDrive(gauth)

if __name__ == "__main__":
    drive = authenticate_drive()
    print("Google Drive authentication successful!")
