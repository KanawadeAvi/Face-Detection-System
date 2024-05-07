
from flask import Flask, render_template, request, redirect, url_for, session
import os
import cv2
import face_recognition
import base64
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = os.urandom(24)


client = MongoClient("mongodb://localhost:27017")
db = client["face_database"]
collection = db["faces"]


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        image_data = request.form['imageData']
        
        # Check if the username already exists in the database
        existing_user = collection.find_one({'username': username})
        if existing_user:
            session['message'] = 'Username already exists,Try using another One!!!'
            return redirect(url_for('index'))
        
        
        img_bytes = base64.b64decode(image_data.split(",")[1])
        
        # Save image to file
        with open('static/images/{}.jpg'.format(username), 'wb') as f:
            f.write(img_bytes)

        # Save username and image filename to database
        result = collection.insert_one({'username': username, 'image': '{}.jpg'.format(username)})
        if result.inserted_id:
            session['message'] = 'Signup successfully!!'
        else:
            session['message'] = 'Signup failed, Try Again'
        return redirect(url_for('index'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        image_data = request.form['imageData']
        
        # Save temporary image for face recognition
        with open('static/images/temp.jpg', 'wb') as f:
            f.write(base64.b64decode(image_data.split(",")[1]))
        
      
        temp_image = face_recognition.load_image_file('static/images/temp.jpg')
        
        # Detect faces in captured image
        face_locations = face_recognition.face_locations(temp_image)
        if len(face_locations) == 1:  # Ensure only one face is detected
         
            face_encoding = face_recognition.face_encodings(temp_image)[0]
          
            similar_faces = collection.find({})
            for face in similar_faces:
                stored_face_path = 'static/images/{}'.format(face['image'])
                stored_face = face_recognition.load_image_file(stored_face_path)
                stored_face_encoding = face_recognition.face_encodings(stored_face)[0]
          
                matches = face_recognition.compare_faces([stored_face_encoding], face_encoding)
                if any(matches):
                    session['username'] = face['username']
                    session['message'] = 'Login successfully'
                    return redirect(url_for('home'))
            session['message'] = 'Try again'
            return redirect(url_for('index')) 
        else:
            session['message'] = 'Try again,Face is not Matched in Database'
            return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/home')
def home():
    if 'username' in session:
        username = session['username']
        return render_template('home.html', username=username)
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    session['message'] = 'Logout successfully'
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
