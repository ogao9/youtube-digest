import json
import os
import pickle
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from pytube import YouTube

'''
    {
        "playlist_title1": [
            {
                "title": "title",
                "thumbnail_url": "thumbnail_url",
                "channel": "channel",
                "video_url": "video_url",
                "description": "description",
                "published_at": "published_at"
            }
        ]
    }
'''
playlist_info = {}

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
    
    # print("retrieve_video_urls: ", response)
    # with open("playlists.json", "w") as fout: 
    #     json.dump(response, fout)

    get_all_playlist_videos(youtube, response.get("items", []))


def get_all_playlist_videos(youtube, playlists):
    # Get ALL playlists, list videos
    for playlist in playlists:
        id = playlist["id"]
        playlist_title = playlist["snippet"]["title"]
        
        playlist_info[playlist_title] = []
        
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
            video_obj = {
                "title": playlist_item["snippet"]["title"],
                "thumbnail_url": playlist_item["snippet"]["thumbnails"]["default"]["url"],
                "channel": playlist_item["snippet"]["videoOwnerChannelTitle"],
                "video_url": "https://www.youtube.com/watch?v=" + playlist_item["contentDetails"]["videoId"],
                "published_at": playlist_item["snippet"]["publishedAt"],
            }
            playlist_info[playlist_title].append(video_obj)
            
            download_video(playlist_item, playlist_title)
            

def download_video(playlist_item, playlist_title):
    # API call download
    video_title = playlist_item["snippet"]["title"]
    video_id = playlist_item["contentDetails"]["videoId"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    
    # travel_url1 = "https://www.youtube.com/watch?v=nV8zOhYBHP4"
    # travel_url2 = "https://www.youtube.com/watch?v=t-mn6LXJ2jY"

    # gym_1 = "https://www.youtube.com/watch?v=jLvqKgW-_G8"
    # gym_2 = "https://www.youtube.com/watch?v=8LJ3Q3Fsrzs"
    
    # playlist_title = "travel"
    # video_title = "travel2"
    # video_url = travel_url2
    # print("Downloading video...", video_url)
    
    output_path = f"cdownloads/{playlist_title}/{video_id}/"
    video_path = output_path
    video_filename = f"{video_id}.mp4"
    audio_path = output_path
    audio_filename = f"{video_id}.mp3"
    
    # Download video and rename
    video = YouTube(video_url).streams.filter(
        subtype='mp4', res="720p").first().download(output_path=video_path, filename=video_filename)

    # # Download audio and rename
    audio = YouTube(video_url).streams.filter(
        only_audio=True).first().download(output_path=audio_path, filename=audio_filename)


def download_all_videos():
    """
    This is the function that the API endpoint calls calls
    """
    retrieve_video_urls()
    return playlist_info


# For testing
if __name__ == "__main__":
    retrieve_video_urls()

