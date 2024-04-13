import json
import os
import pickle
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import requests
from pytube import YouTube

# Define scopes for accessing YouTube data
scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

def authenticate():
    # Start OAuth flow to get user consent
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        "client_secrets.json", scopes)
    credentials = flow.run_console()

    # Save credentials for future use
    with open('token.pickle', 'wb') as token:
        pickle.dump(credentials, token)

def retrieve_video_urls():
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    # Load saved credentials or authenticate
    try:
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)
    except FileNotFoundError:
        authenticate()

    # Create YouTube API client with the credentials
    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

    # Make request to get user's playlists
    request = youtube.playlists().list(
        part="contentDetails,id,snippet",
        mine=True
    )
    response = request.execute()
    print(response)
    with open("playlists.json", "w") as fout: 
        json.dump(response, fout)

    # get_digest_videos(youtube, response.get("items", []))
    get_all_playlist_videos(youtube, response.get("items", []))

def get_digest_videos(youtube, playlists):
    # Get Digest Playlist, list videos
    digest_id = ""
    for playlist in playlists:
        if playlist["snippet"]["title"] == "digest":
            digest_id = playlist["id"]
            break
    if digest_id == "":
        print("digest not found")
        return
    request = youtube.playlistItems().list(
        part="contentDetails,id,snippet,status",
        playlistId=digest_id
    )
    response = request.execute()
    print(response)
    with open("digest-videos.json", "w") as fout: 
        json.dump(response, fout)

def get_all_playlist_videos(youtube, playlists):
    # Get ALL playlists, list videos
    for playlist in playlists:
        id = playlist["id"]
        request = youtube.playlistItems().list(
            part="contentDetails,id,snippet,status",
            playlistId=id
        )
        response = request.execute()
        print(response)
        with open(f"playlist-item-{id}.json", "a") as fout: 
            json.dump(response, fout)

            # Dump just the id, title, description of video
        playlist_items = response.get("items", [])
        for playlist_item in playlist_items:
            download_video(playlist_item)


def download_video(playlist_item):
    video_id = playlist_item["contentDetails"]["videoId"]
    print("video_id: ", video_id)
    # API call download @ videoId
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    print("video_url: ", video_url)

    # Download the video
    print("Downloading...")
    pyt = YouTube(video_url)
    pyt.streams.filter(progressive=True, file_extension='mp4').first().download()
    
    print("...finished downloading")
    
    # response = requests.get(video_url)
    # if response.status_code == 200:
    #     with open(f"data/{video_id}.mp4", "wb") as fout:
    #         fout.write(response.content)
    #         print(f"Video '{video_id}' downloaded successfully.")
    # else:
    #     print(f"Failed to download video '{video_id}'. Status code: {response.status_code}")

# retrieve_video_urls()

def test_download_video(video_url):
    print("video_url: ", video_url)
    print("Downloading...")
    
    pyt = YouTube(video_url)
    pyt.streams.filter(progressive=True, file_extension='mp4').first().download()
    
    print("...finished downloading")

test_download_video("https://www.youtube.com/watch?v=YLslsZuEaNE")