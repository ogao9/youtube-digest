import google.generativeai as genai
import os
import cv2
import shutil
from moviepy.editor import VideoFileClip

# genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
genai.configure(api_key="AIzaSyAb0ddbk-B7BrSo-YTubBCkQRBijK9oz00")

# Create or cleanup existing extracted image frames directory.
FRAME_EXTRACTION_DIRECTORY = "content/frames"
FRAME_PREFIX = "_frame"
def create_frame_output_dir(output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    else:
        shutil.rmtree(output_dir)
        os.makedirs(output_dir)

def extract_frame_from_video(video_file_path):
    print(f"Extracting {video_file_path} at 1 frame per second. This might take a bit...")
    
    create_frame_output_dir(FRAME_EXTRACTION_DIRECTORY)
    output_file_prefix = os.path.basename(video_file_path).replace('.', '_')
    
    vidcap = cv2.VideoCapture(video_file_path)
    fps = vidcap.get(cv2.CAP_PROP_FPS)
    frame_duration = 1 / fps  # Time interval between frames (in seconds)
    frame_count = 0
    count = 0

    while vidcap.isOpened():
        success, frame = vidcap.read()
        
        if not success: # End of video
            break
        if int(count / fps) == frame_count: # Extract a frame every second
            min = frame_count // 60
            sec = frame_count % 60
            time_string = f"{min:02d}{sec:02d}"
            
            image_name = f"{output_file_prefix}{FRAME_PREFIX}{time_string}.jpg"
            output_filename = os.path.join(FRAME_EXTRACTION_DIRECTORY, image_name)
            cv2.imwrite(output_filename, frame)
            frame_count += 1
            
        count += 1
    
    vidcap.release() # Release the capture object\n",
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


def upload_image_files():
    # Process each frame in the output directory
    files = os.listdir(FRAME_EXTRACTION_DIRECTORY)
    files = sorted(files)
    
    files_to_upload = []
    for file in files:
        files_to_upload.append(
            File(file_path=os.path.join(FRAME_EXTRACTION_DIRECTORY, file)))

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

def extract_audio_from_video(video_file_name, audio_output_file_name):
    # Load the video clip
    video_clip = VideoFileClip(video_file_name)

    # Extract the audio from the video clip
    audio_clip = video_clip.audio

    # Write the audio to a separate file
    audio_clip.write_audiofile(audio_output_file_name)

    # Close the video and audio clips
    audio_clip.close()
    video_clip.close()

    print("Audio extraction successful!")


def upload_audio(audio_output_file_name):
    uploaded = genai.upload_file(path=audio_output_file_name)
    
    return [uploaded]


def call_model(prompt, files):
    # Set the model to Gemini 1.5 Pro.
    model = genai.GenerativeModel(model_name="models/gemini-1.5-pro-latest")

    # Make the LLM request.
    request = [prompt] + files
    response = model.generate_content(request, request_options={"timeout": 1000})
    
    print("\n\nGemini Response:")
    print(response.text)


def main(video_file_name, audio_output_file_name):
    print("Program Starting...")
    
    extract_frame_from_video(video_file_name)
    uploaded_image_files = upload_image_files()

    extract_audio_from_video(video_file_name, audio_output_file_name)
    uploaded_audio_files = upload_audio(audio_output_file_name)
    
    # Create the prompt.
    prompt = "I have uploaded an audio file of a video followed by visual frames of the video. Provide a brief summary of the video."
    
    request_files = uploaded_audio_files
    for file in uploaded_image_files:
        if (file.response != ""):
            request_files.append(file.timestamp)
            request_files.append(file.response)
    
    call_model(prompt, request_files)

video_file_name = "gym.mp4"
audio_output_file_name="audio.mp3"
main(video_file_name, audio_output_file_name)