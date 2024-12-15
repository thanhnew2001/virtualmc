import os
import replicate
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
    if 'image' not in request.files or 'audio' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    # Handle image + audio or video + audio uploads based on selection
    image_file = request.files.get('image')
    audio_file = request.files['audio']
    video_file = request.files.get('video')

    # Ensure the static folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Process image + audio
    if image_file and allowed_file(image_file.filename) and audio_file and allowed_file(audio_file.filename):
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

        # Call Replicate API to generate the video (using the image and audio)
        output = replicate.run(
            "devxpy/cog-wav2lip:8d65e3f4f4298520e079198b493c25adfc43c058ffec924f2aefc8010ed25eef",
            input=input_data
        )
        print(output)


        generated_video_url = url_for('serve_file', filename='generated_video.mp4', _external=True)

        return jsonify({'video_url': output.video_url})

    elif video_file and allowed_file(video_file.filename) and audio_file and allowed_file(audio_file.filename):
        # Process video + audio
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_file.filename)
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_file.filename)
        video_file.save(video_path)
        audio_file.save(audio_path)

        # Generate full URL for the video and audio
        video_url = url_for('serve_file', filename=video_file.filename, _external=True)
        audio_url = url_for('serve_file', filename=audio_file.filename, _external=True)

        input_data = {
            "face": video_url,  # Full URL for the face (video)
            "audio": audio_url,  # Full URL for the audio
            "fps": 25,
            "pads": "0 10 0 0",  # Padding for the detected face bounding box
            "smooth": True,  # Smooth face detections
            "resize_factor": 1  # No resizing
        }
        print(input_data)

        # Call Replicate API to generate the video (using the video and audio)
        output = replicate.run(
            "devxpy/cog-wav2lip:8d65e3f4f4298520e079198b493c25adfc43c058ffec924f2aefc8010ed25eef",
            input=input_data
        )
        print(output)

        generated_video_url = url_for('serve_file', filename='generated_video.mp4', _external=True)

        return jsonify({'video_url': output.video_url})

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
