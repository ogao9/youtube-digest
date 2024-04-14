import google.generativeai as genai
import os
import cv2
import re
import json
from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

FRAME_EXTRACTION_DIRECTORY = "cdownloads"
CACHE_DIRECTORY = "moreknowledge"
FRAME_PREFIX = "_frame"

def remove_substrings(s):
    s = s.replace("```json", "", 1)  # Remove the first occurrence of ```json
    s = s[::-1].replace("```"[::-1], "", 1)[::-1]  # Remove the last occurrence of ```
    return s

def save_json_to_file(json_data, filename):
    with open(filename, 'w') as f:
        json.dump(json_data, f, indent=4) # Use indent for better readability


def extract_titles(video_file_path):
    pattern = r'downloads/(?P<playlist_title>[^/]*)/(?P<video_title>[^/]*)/video.mp4'
    match = re.search(pattern, video_file_path)
    if match:
        return match.group('playlist_title'), match.group('video_title')
    else:
        return None, None


def create_frame_output_dir(output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)


def extract_frame_from_video(video_file_path):
    print(f"Extracting {video_file_path} at 1 frame per second. This might take a bit...")
    playlist_title, video_title = extract_titles(video_file_path)
    
    output_dir = FRAME_EXTRACTION_DIRECTORY + "/" + playlist_title + "/" + video_title + "/" + "frames"
    create_frame_output_dir(output_dir)
    
    vidcap = cv2.VideoCapture(video_file_path)
    fps = vidcap.get(cv2.CAP_PROP_FPS)
    frame_count = 0
    count = 0
    
    frame_duration = 1 # Time interval between frames (in seconds)

    while vidcap.isOpened():
        success, frame = vidcap.read()
        
        if not success: # End of video
            break
        if int(count / fps) == frame_count*frame_duration: # Extract a frame every second
            min = frame_count // 60
            sec = frame_count % 60
            time_string = f"{min:02d}{sec:02d}"
            
            image_name = f"{FRAME_PREFIX}{time_string}.jpg"
            output_filename = os.path.join(output_dir, image_name)
            
            cv2.imwrite(output_filename, frame)
            frame_count += 1
            
        count += 1
    
    vidcap.release()
    print(f"Completed video frame extraction!\nExtracted: {frame_count} frames\n\n")

class File:
    def __init__(self, file_path: str, display_name: str = "test"):
        self.file_path = file_path
        self.response = ""
        
        if display_name:
            self.display_name = display_name
            self.timestamp = get_timestamp(file_path)

    def set_file_response(self, response):
        self.response = response


def get_timestamp(filename):
    """Extracts the frame count (as an integer) from a filename with the format
        'output_file_prefix_frame0000.jpg'.
    """
    parts = filename.split(FRAME_PREFIX)
    if len(parts) != 2:
        return None  # Indicates the filename might be incorrectly formatted
    
    splitted = parts[1].split('.')
    return splitted[0]


def upload_image_files(video_file_path):
    # Process each frame in the output directory
    playlist_title, video_title = extract_titles(video_file_path)
    frames_dir = FRAME_EXTRACTION_DIRECTORY + "/" + playlist_title + "/" + video_title + "/" + "frames"
    files = os.listdir(frames_dir)
    files = sorted(files)
    
    files_to_upload = []
    for file in files:
        files_to_upload.append(
            File(file_path=os.path.join(frames_dir, file)))

    # Upload the files to the API
    # Only upload a 10 second slice of files to reduce upload time.
    # Change full_video to True to upload the whole video.
    full_video = False

    uploaded_image_files = []
    print(f'Uploading {len(files_to_upload) if full_video else 10} files. This might take a bit...')

    for file in files_to_upload if full_video else files_to_upload[:10]:
        print(f'Uploading: {file.file_path}...')
        response = genai.upload_file(path=file.file_path)
        file.set_file_response(response)
        uploaded_image_files.append(file)

    print(f"Completed file uploads! Uploaded: {len(uploaded_image_files)} files \n\n")
    return files_to_upload


def upload_audio(audio_file_name):
    uploaded = genai.upload_file(path=audio_file_name)
    return [uploaded]


def preprocess():
    print("\nPreprocessing start.\n")
    
    # Would do this if had time
    # extract_frame_from_video(video_file_name)
    # uploaded_image_files = upload_image_files(video_file_name)
    
    prompt = """
        I have uploaded an audio file of a video.
        First, provide a brief summary of the video.
        Then, provide timestamps of the key moments in the video with their respective descriptions.
    """
    
    # for root, dirs, files in os.walk(FRAME_EXTRACTION_DIRECTORY):
    #     for file in files:
            
    #         if file.endswith('.mp3'):
    #             # get part string of file without the .mp3
    #             file_no_suffix = file[:-4]
                
    #             # check that file is not already in the moreknowledge directory
    #             if file_no_suffix in os.listdir(CACHE_DIRECTORY):
    #                 continue
                
    #             print(file_no_suffix)
    #             audio_file_name = os.path.join(root, file)
    
    #             uploaded_audio_files = upload_audio(audio_file_name)
    #             request_files = uploaded_audio_files
                
    #             # Make the LLM request.
    #             model = genai.GenerativeModel(model_name="models/gemini-1.5-pro-latest")

    #             request = [prompt] + request_files
    #             response = model.generate_content(request, request_options={"timeout": 10000})
                
    #             print("\n\nGemini Response:")
    #             print(response.text)
                
    #             # save text to txt file
    #             output_path=os.path.join(CACHE_DIRECTORY, file_no_suffix)
    #             with open(output_path, 'w') as f:
    #                 f.write(response.text)
    
    file_no_suffix = "WJou7DxdP4o"
    audio_file_name = f"cdownloads/travel/food/{file_no_suffix}/{file_no_suffix}.mp3"
    
    uploaded_audio_files = upload_audio(audio_file_name)
    request_files = uploaded_audio_files
    
    # Make the LLM request.
    model = genai.GenerativeModel(model_name="models/gemini-1.5-pro-latest")

    request = [prompt] + request_files
    response = model.generate_content(request, request_options={"timeout": 10000})
    
    print("\n\nGemini Response:")
    print(response.text)
    
    # save text to txt file
    output_path=os.path.join(CACHE_DIRECTORY, file_no_suffix)
    with open(output_path, 'w') as f:
        f.write(response.text)
        
    print("\nPreprocessing done.\n")


def get_answer(user_prompt):
    res_obj = {}
    dir = CACHE_DIRECTORY
    files = os.listdir(dir)
    files = sorted(files)
    text_data = []
    
    for file in files:
        file_path=os.path.join(dir, file)
        
        with open(file_path) as f:
            id = f"The id of this video is {file}. "
            text_data.append(id + f.read())
    
    model = genai.GenerativeModel(model_name="models/gemini-1.5-pro-latest")
    
    base_prompt = """I am uploading several files that contain the summary and timestamps of key moments in several respective videos. 
    Based on the contents of relevant files, please answer this prompt in one paragraph or less. Also, do not include the video id in the response please.
    """
    
    print("\n\nGemini Response:")
    
    prompt1 = base_prompt + " " + user_prompt
    request = [prompt1] + text_data
    
    chat = model.start_chat(history=[])
    response = chat.send_message(request)
    res_obj["summary"] = response.text
    print(response.text)
    
    prompt2 = """
    Now, provide the starting timestamp of a maximum of 3 key moments in each video with their respective descriptions 
    that were most relevant to answering the previous prompt. Please respond in json format like this:
    {
        "id of video": [{"Timestamp" : "mm:ss", "Description" : "Description of the key moment"}, {"timestamp" : "mm:ss", "Description" : "Description of the key moment"}],
        "id of video": [{"Timestamp" : "mm:ss", "Description" : "Description of the key moment"}, {"timestamp" : "mm:ss", "Description" : "Description of the key moment"}],
    }
    """

    response = chat.send_message(prompt2)
    print(response.text)
    
    json_res = remove_substrings(response.text)
    # convert json string to dictionary
    json_res = json.loads(json_res)
    res_obj["timestamps"] = json_res
    
    # conver the timestamp from mm:ss to a number
    for key, value in res_obj["timestamps"].items():
        for i in range(len(value)):
            time = value[i]["Timestamp"]
            min, sec = time.split(":")
            time = int(min) * 60 + int(sec)
            value[i]["video_url"] = f"https://www.youtube.com/watch?v={key}&t={time}"
    
    return res_obj
    
# For testing
if __name__ == "__main__":
    preprocess()
