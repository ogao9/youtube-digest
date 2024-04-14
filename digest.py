import json
import os
import pickle
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from pytube import YouTube
import moviepy.editor as mpe

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
    print("retrieve_video_urls: ", response)
    
    # with open("playlists.json", "w") as fout: 
    #     json.dump(response, fout)

    get_digest_videos(youtube, response.get("items", []))
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
    
    # print("get_digest_videos: ", response)
    # with open("digest-videos.json", "w") as fout: 
    #     json.dump(response, fout)

def get_all_playlist_videos(youtube, playlists):
    # Get ALL playlists, list videos
    for playlist in playlists:
        id = playlist["id"]
        request = youtube.playlistItems().list(
            part="contentDetails,id,snippet,status",
            playlistId=id
        )
        response = request.execute()
        
        # print(response)
        # Dump just the id, title, description of video
        # with open(f"playlist-item-{id}.json", "a") as fout: 
        #     json.dump(response, fout)

        playlist_items = response.get("items", [])
        for playlist_item in playlist_items:
            download_video(playlist_item)


def download_video(playlist_item):
    # API call download
    video_id = playlist_item["contentDetails"]["videoId"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    print("Downloading video...", video_url)
    
    vname = "clip.mp4"
    aname = "audio.mp3"
    
    # Download video and rename
    video = YouTube(video_url).streams.filter(
        subtype='mp4', res="720p").first().download()
    os.rename(video, vname)

    # # Download audio and rename
    audio = YouTube(video_url).streams.filter(only_audio=True).first().download()
    os.rename(audio, aname)
    
    # Delete video and audio to keep the result
    os.remove(vname)
    os.remove(aname)

    # ----- mpe method but we don't even need to do this!! -----
    # Setting the audio to the video
    # video = mpe.VideoFileClip(vname)
    # audio = mpe.AudioFileClip(aname)
    # final = video.set_audio(audio)

    # # Output result
    # final.write_videofile("video.mp4")


def main():
    retrieve_video_urls()
    
    
if __name__ == "__main__":
    main()