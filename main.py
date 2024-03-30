import sys

import face_recognition
from flask import Flask, render_template, request, json
import os
from PIL import Image
from io import BytesIO

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'image' in request.files:
            image = request.files['image']
            app.logger.info('Received image file: %s', image.filename)
            # Convert the image to RGB mode
            img = Image.open(BytesIO(image.read()))
            img = img.convert('RGB')
            img_path = 'unknown.jpg'  # Saving in the root directory with the name unknown.jpg
            img.save(img_path, 'JPEG')
            app.logger.info('Image saved to: %s', img_path)
            app.logger.info('into login with face')
            return json.dumps(login_with_face())
        else:
            app.logger.error('No image received.')
            return 'No image received.', 400
    except Exception as e:
        error_message = f'An error occurred: {str(e)}'
        app.logger.error(error_message)
        print(error_message, file=sys.stderr)  # Display error on Flask terminal
        return error_message, 500


def login_with_face():
    try:
        app.logger.info('Into login_with_faces')
        known_face_encodings = []
        known_face_emails = []


        # Load known face encodings and corresponding emails
        for file in os.listdir("known_faces"):
            if file.endswith(".jpg") or file.endswith(".png"):
                image = face_recognition.load_image_file(f"known_faces/{file}")
                encoding = face_recognition.face_encodings(image)[0]
                known_face_encodings.append(encoding)
                known_face_emails.append(file.split(".")[0])

        unknown_image = face_recognition.load_image_file("unknown.jpg")
        unknown_encoding = face_recognition.face_encodings(unknown_image)

        app.logger.info('about to match faces')

        # Check if face is detected
        if len(unknown_encoding) > 0:
            # Compare with known faces
            results = face_recognition.compare_faces(known_face_encodings, unknown_encoding[0], tolerance=0.5)
            app.logger.info('matching faces')
            # Check if any match is found
            if True in results:
                matched_email = known_face_emails[results.index(True)]
                app.logger.info('Face matched')
                return {"status": "success", "message": f"Logged in successfully: {matched_email}"}
            else:
                app.logger.info('Face unmatched')
                return {"status": "error", "message": "User not found."}
        else:
            app.logger.info('Face not detected')
            return {"status": "error", "message": "No face detected."}
    except Exception as e:
        error_message = f'An error occurred in face recognition: {str(e)}'
        app.logger.error(error_message)
        print(error_message, file=sys.stderr)  # Display error on Flask terminal
        return {"status": "error", "message": "Internal server error."}

# Function to perform login using email and password
def login_with_email(email, password):
    try:
        # Check if the file for the email exists
        if os.path.exists(os.path.join("known_emailpass", f"{email}.txt")):
            # Read the password from the file
            with open(os.path.join("known_emailpass", f"{email}.txt"), "r") as file:
                saved_password = file.readline().strip()

            # Check if the entered password matches the saved password
            if password == saved_password:
                return {"status": "success", "message": f"Logged in successfully: {email}"}
            else:
                return {"status": "error", "message": "Incorrect email or password."}
        else:
            return {"status": "error", "message": "User not found."}
    except Exception as e:
        error_message = f'An error occurred in email login: {str(e)}'
        app.logger.error(error_message)
        print(error_message, file=sys.stderr)  # Display error on Flask terminal
        return {"status": "error", "message": "Internal server error."}

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    if "email" in data and "password" in data:
        return json.dumps(login_with_email(data["email"], data["password"]))
    else:

        return json.dumps(login_with_face())

if __name__ == "__main__":
    app.run(debug=True)
