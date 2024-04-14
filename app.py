from flask import Flask, render_template, request, redirect, url_for
from digest import download_all_videos
from gemini import get_answer, preprocess
from threading import Thread
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

"""
Why this is our tool better than a traditional text-based tool?
YOU get to control the content we are drawing answers from
Demo Ideas:
1. Gym (3 video about back exercises)
2. Coding (I don't think this is a great example)
3. Travel
"""


@app.route('/initialize/', methods=['GET'])
def initalize():
    """
    1. Download all videos in each of the user's playlists
    2. Returns a playlist info object
    3. Do some pre-processing to get the relevant information
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
    """
    res_obj = download_all_videos()
    Thread(target=preprocess).start()
    return res_obj


@app.route('/submit_prompt/', methods=['GET'])
def submit_prompt():
    """
    Input: prompt from the user
    Output: relevant information in json format, like timestamps and summaries
    {
        summary: "Summary of the knowledge base",
        timestamps: [
            {
                timestamp: number,
                description: "Description of the video at this timestamp"
            }
        ]
    }
    """
    user_prompt = request.args.get("prompt")
    response = get_answer(user_prompt)
    
    return response


if __name__ == '__main__':
    app.run(debug=True)
