import os
import replicate
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Configure the app for file uploads and static files
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'mp4', 'wav', 'mp3'}
app.secret_key = 'your-secret-key'  # For session and security

# Replicate API setup
replicate_client = replicate.Client(api_token="your-replicate-api-token")

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

    if image_file and allowed_file(image_file.filename) and audio_file and allowed_file(audio_file.filename):
        # Process image + audio
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_file.filename)
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_file.filename)
        image_file.save(image_path)
        audio_file.save(audio_path)

        # Call Replicate API to generate the video (using image)
        output = replicate_client.run(
            "devxpy/cog-wav2lip:8d65e3f4f4298520e079198b493c25adfc43c058ffec924f2aefc8010ed25eef",
            input={
                "face": image_path,  # Image with face for lip-sync
                "audio": audio_path,  # Audio file
                "fps": 25,
                "pads": "0 10 0 0",  # Padding for the detected face bounding box
                "smooth": True,  # Smooth face detections
                "resize_factor": 1  # No resizing
            }
        )
        video_output_url = output[0]
        return jsonify({'video_url': video_output_url})

    elif video_file and allowed_file(video_file.filename) and audio_file and allowed_file(audio_file.filename):
        # Process video + audio
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_file.filename)
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_file.filename)
        video_file.save(video_path)
        audio_file.save(audio_path)

        # Call Replicate API to generate the video (using video)
        output = replicate_client.run(
            "devxpy/cog-wav2lip:8d65e3f4f4298520e079198b493c25adfc43c058ffec924f2aefc8010ed25eef",
            input={
                "face": video_path,  # Video with face for lip-sync
                "audio": audio_path,  # Audio file
                "fps": 25,
                "pads": "0 10 0 0",  # Padding for the detected face bounding box
                "smooth": True,  # Smooth face detections
                "resize_factor": 1  # No resizing
            }
        )
        video_output_url = output[0]
        return jsonify({'video_url': video_output_url})

    return jsonify({'error': 'Invalid file format. Only image, audio, and video files are allowed.'}), 400


if __name__ == '__main__':
    # Create uploads directory if not exists
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)
