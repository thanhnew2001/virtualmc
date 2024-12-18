import os
import replicate
from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
import requests
import uuid

app = Flask(__name__)

ALLOWED_IP = socket.gethostbyname(socket.gethostname())
print(f"Allowed IP: {ALLOWED_IP}")  # Prints the backend's current IP



# Configure the app for file uploads
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'mp4', 'wav', 'mp3'}
app.secret_key = 'your-secret-key'  # For session and security

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
    
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    client_ip = request.remote_addr
    if client_ip != ALLOWED_IP:
        return jsonify({"error": "Access denied: Unauthorized IP"}), 403
        
    # Handle image + audio or video + audio uploads based on selection
    image_file = request.files.get('image')
    audio_file = request.files['audio']
    video_file = request.files['video']
    print(audio_file.filename)
    file_type = request.form.get("file_type")



    # Ensure the static folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Process image + audio
    if file_type=='image':
        # Save the image and audio files
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_file.filename)
        image_file.save(image_path)
        audio_file.save(audio_path)

        # Generate full URLs for the image and audio
        image_url = url_for('serve_file', filename=image_file.filename, _external=True)
        audio_url = url_for('serve_file', filename=audio_file.filename, _external=True)

        # Prepare input data for the Replicate API
        input_data = {
            "face": image_url,  # Full URL for the face (image)
            "audio": audio_url,  # Full URL for the audio
            "fps": 25,
            "pads": "0 10 0 0",  # Padding for the detected face bounding box
            "smooth": True,  # Smooth face detections
            "resize_factor": 1  # No resizing
        }
        print(input_data)

        try:
            # Call Replicate API to generate the video (using image and audio)
            output = replicate.run(
                "devxpy/cog-wav2lip:8d65e3f4f4298520e079198b493c25adfc43c058ffec924f2aefc8010ed25eef",
                input=input_data
            )

            # The output is a URL to the generated video (MP4)
            video_url = output  # This should be the URL returned by Replicate API

            # Now download the video from the URL and save it locally
            unique_file_name = f"generated_video_{uuid.uuid4().hex}.mp4"
            local_video_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_file_name)
            download_success = download_file(video_url, local_video_path)

            if download_success:
                # Generate a public URL for the saved video
                public_video_url = url_for('static',  filename=f'uploads/{unique_file_name}', _external=True)
                return jsonify({'video_url': public_video_url})

            else:
                return jsonify({'error': 'Failed to download the video'}), 500

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    if file_type=='video':
        print("TEsting video")
        # Process video + audio
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_file.filename)
        print(video_path)
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_file.filename)
        video_file.save(video_path)
        audio_file.save(audio_path)

        # Generate full URL for the video and audio
        video_url = url_for('serve_file', filename=video_file.filename, _external=True)
        audio_url = url_for('serve_file', filename=audio_file.filename, _external=True)
        print(video_url)

        input_data = {
            "face": video_url,  # Full URL for the face (video)
            "audio": audio_url,  # Full URL for the audio
            "fps": 25,
            "pads": "0 10 0 0",  # Padding for the detected face bounding box
            "smooth": True,  # Smooth face detections
            "resize_factor": 1  # No resizing
        }
        print(input_data)

        try:
            # Call Replicate API to generate the video (using image and audio)
            output = replicate.run(
                "devxpy/cog-wav2lip:8d65e3f4f4298520e079198b493c25adfc43c058ffec924f2aefc8010ed25eef",
                input=input_data
            )

            # The output is a URL to the generated video (MP4)
            video_url = output  # This should be the URL returned by Replicate API

            # Now download the video from the URL and save it locally
            unique_file_name = f"generated_video_{uuid.uuid4().hex}.mp4"
            local_video_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_file_name)
            download_success = download_file(video_url, local_video_path)

            if download_success:
                # Generate a public URL for the saved video
                public_video_url = url_for('static',  filename=f'uploads/{unique_file_name}', _external=True)
                return jsonify({'video_url': public_video_url})

            else:
                return jsonify({'error': 'Failed to download the video'}), 500

        except Exception as e:
            return jsonify({'error': str(e)}), 500

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
