import os
import json
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials

def authenticate_drive():
    # Read the service account JSON from GitHub Secrets (stored in an env variable)
    service_account_info = json.loads(os.environ["GDRIVE_SERVICE_ACCOUNT_JSON"])
    
    # Define the scope and create credentials
    scope = ["https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(service_account_info, scope)
    
    # Authenticate PyDrive
    gauth = GoogleAuth()
    gauth.credentials = credentials
    return GoogleDrive(gauth)

if __name__ == "__main__":
    drive = authenticate_drive()
    print("Google Drive authentication successful!")
