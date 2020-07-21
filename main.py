import httplib2
import os
import tempfile
import requests
from fastapi import FastAPI, HTTPException
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow


CLIENT_SECRETS_FILE = "client_secret_883479366060-791bce9ddf0gd1gug60m2uoh8ss7akdl.apps.googleusercontent.com.json"
SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl", "https://www.googleapis.com/auth/youtube.upload"]
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To run this code you will need to populate the client_secrets.json file
found at:

   %s

with information from the API Console
https://console.developers.google.com/

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(
    os.path.join(os.path.dirname(__file__), CLIENT_SECRETS_FILE)
)


def get_authenticated_service(user_id, args=None):
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    flow = flow_from_clientsecrets(
        CLIENT_SECRETS_FILE, scope=SCOPES, message=MISSING_CLIENT_SECRETS_MESSAGE
    )
    try:
        file_name = "tokens/{}.token.json".format(user_id)
        storage = Storage(file_name)
        credentials = storage.get()
        assert credentials and not credentials.invalid, "Invalid credentials"
    except:
        credentials = run_flow(flow, storage, args)

    return build(
        YOUTUBE_API_SERVICE_NAME,
        YOUTUBE_API_VERSION,
        http=credentials.authorize(httplib2.Http()),
    )


def update_thumbnail(youtube_service, video_id, thumbnail_file):
    request = youtube_service.thumbnails().set(
        videoId=video_id,
        media_body=MediaFileUpload(thumbnail_file)
    )
    response = request.execute()
    return response


app = FastAPI()


@app.get("/")
def read_root():
    return {"msg": "ok"}

@app.get("/authorize")
def authorize_user(user_id: str):
    """
    Retrieves & stores access tokens
    """
    # WIP: DOES NOT WORK - crashes uvicorn
    # TODO: VERIFY user_id! Ideally using a JWT before we call this API.
    # TODO: Replace with proper logger
    print("Authorizing user {}".format(user_id))
    try:
        youtube = get_authenticated_service(user_id)
        return {'msg': 'Authorized!', 'user_id': user_id}
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=403, detail=str(e))

@app.post("/{video_id}")
def upload_thumbnail_wrapper(video_id: str, body: dict):
    """
    Uploads a thumbnail to a Youtube video.
    """
    # TODO: VERIFY this user_id! Ideally using a JWT before we call this API.
    user_id = body["user_id"]
    # TODO: Replace with proper logger
    print("Processing video with ID {} for user {}".format(video_id, user_id))
    try:
        thumbnail_url = body["thumbnail_url"]
        print(thumbnail_url)
        youtube = get_authenticated_service(user_id)
        # upload thumbnail
        with tempfile.NamedTemporaryFile() as fp:
            thumbnail_content = requests.get(thumbnail_url).content
            fp.write(thumbnail_content)
            print(fp.name)
            # response = fp.name
            response = update_thumbnail(youtube, video_id, fp.name)
        return response
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=403, detail=str(e))


if __name__ == "__main__":
    user_id = "tictaclearn@contentready.co"
    resp = authorize_user(user_id)
    print(resp)
