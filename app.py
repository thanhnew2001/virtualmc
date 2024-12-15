import os
import uuid
import requests
from flask import Flask, render_template, request, jsonify, send_from_directory, url_for

app = Flask(__name__)

# Configure the app for file uploads
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'mp4', 'wav', 'mp3'}
app.secret_key = 'your-secret-key'  # For session and security

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

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

    # Process image + audio or video + audio uploads
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

        # Call Replicate API to generate the video (using the image and audio)
        output = replicate.run(
            "devxpy/cog-wav2lip:8d65e3f4f4298520e079198b493c25adfc43c058ffec924f2aefc8010ed25eef",
            input=input_data
        )
        video_url = output  # Assuming output is the URL to the generated video

        # Generate a random filename for the video
        video_filename = str(uuid.uuid4()) + '.mp4'
        local_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)

        # Download the video from the URL returned by Replicate API
        try:
            response = requests.get(video_url, stream=True)
            if response.status_code == 200:
                # Save the video in chunks
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                # Return the URL to the generated video file
                return jsonify({'video_url': url_for('static', filename=f'uploads/{video_filename}', _external=True)})

            else:
                return jsonify({'error': 'Error downloading the video file from Replicate API'}), 500
        except Exception as e:
            return jsonify({'error': f'Error downloading the video: {str(e)}'}), 500

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

        # Call Replicate API to generate the video (using the video and audio)
        output = replicate.run(
            "devxpy/cog-wav2lip:8d65e3f4f4298520e079198b493c25adfc43c058ffec924f2aefc8010ed25eef",
            input=input_data
        )
        video_url = output  # Assuming output is the URL to the generated video

        # Generate a random filename for the video
        video_filename = str(uuid.uuid4()) + '.mp4'
        local_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)

        # Download the video from the URL returned by Replicate API
        try:
            response = requests.get(video_url, stream=True)
            if response.status_code == 200:
                # Save the video in chunks
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                # Return the URL to the generated video file
                return jsonify({'video_url': url_for('static', filename=f'uploads/{video_filename}', _external=True)})

            else:
                return jsonify({'error': 'Error downloading the video file from Replicate API'}), 500
        except Exception as e:
            return jsonify({'error': f'Error downloading the video: {str(e)}'}), 500

    return jsonify({'error': 'Invalid file format. Only image, audio, and video files are allowed.'}), 400

# Flask route to serve the generated video from the static folder
@app.route('/static/uploads/<filename>')
def serve_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    # Create uploads directory if not exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
