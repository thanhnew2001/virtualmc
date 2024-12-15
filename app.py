import os
import requests
from flask import Flask, render_template, request, jsonify
import replicate

app = Flask(__name__)

# Configure the app for file uploads
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'mp4', 'wav', 'mp3'}
app.secret_key = 'your-secret-key'  # For session and security

# Replicate API setup (assuming you've already initialized replicate)
# replicate_client = replicate.Client(api_token="your-replicate-api-token")

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Helper function to download file from URL and save it locally
def download_file(url, local_path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Will raise an HTTPError for bad responses
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192): 
                f.write(chunk)
        return True
    except Exception as e:
        print(f"Error downloading the file: {e}")
        return False

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'image' not in request.files and 'video' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    # Handle image + audio or video + audio uploads based on selection
    image_file = request.files.get('image')
    audio_file = request.files['audio']
    video_file = request.files.get('video')

    # Ensure the static folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    if image_file and allowed_file(image_file.filename) and audio_file and allowed_file(audio_file.filename):
        # Process image + audio
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_file.filename)
        image_file.save(image_path)
        audio_file.save(audio_path)

        input_data = {
            "face": image_path,  # Image with face for lip-sync
            "audio": audio_path,  # Audio file
            "fps": 25,
            "pads": "0 10 0 0",  # Padding for the detected face bounding box
            "smooth": True,  # Smooth face detections
            "resize_factor": 1  # No resizing
        }

        try:
            # Call Replicate API to generate the video (using image and audio)
            output = replicate.run(
                "devxpy/cog-wav2lip:8d65e3f4f4298520e079198b493c25adfc43c058ffec924f2aefc8010ed25eef",
                input=input_data
            )

            # The output is a URL to the generated video (MP4)
            video_url = output  # This should be the URL returned by Replicate API

            # Now download the video from the URL and save it locally
            local_video_path = os.path.join(app.config['UPLOAD_FOLDER'], 'generated_video.mp4')
            download_success = download_file(video_url, local_video_path)

            if download_success:
                # Return the local video URL to the client
                return jsonify({'video_url': '/static/uploads/generated_video.mp4'})

            else:
                return jsonify({'error': 'Failed to download the video'}), 500

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    elif video_file and allowed_file(video_file.filename) and audio_file and allowed_file(audio_file.filename):
        # Process video + audio
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_file.filename)
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_file.filename)
        video_file.save(video_path)
        audio_file.save(audio_path)

        input_data = {
            "face": video_path,  # Video with face for lip-sync
            "audio": audio_path,  # Audio file
            "fps": 25,
            "pads": "0 10 0 0",  # Padding for the detected face bounding box
            "smooth": True,  # Smooth face detections
            "resize_factor": 1  # No resizing
        }

        try:
            # Call Replicate API to generate the video (using video and audio)
            output = replicate.run(
                "devxpy/cog-wav2lip:8d65e3f4f4298520e079198b493c25adfc43c058ffec924f2aefc8010ed25eef",
                input=input_data
            )

            # The output is a URL to the generated video (MP4)
            video_url = output  # This should be the URL returned by Replicate API

            # Now download the video from the URL and save it locally
            local_video_path = os.path.join(app.config['UPLOAD_FOLDER'], 'generated_video.mp4')
            download_success = download_file(video_url, local_video_path)

            if download_success:
                # Return the local video URL to the client
                return jsonify({'video_url': '/static/uploads/generated_video.mp4'})

            else:
                return jsonify({'error': 'Failed to download the video'}), 500

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    return jsonify({'error': 'Invalid file format. Only image, audio, and video files are allowed.'}), 400


if __name__ == '__main__':
    # Ensure the uploads directory exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
