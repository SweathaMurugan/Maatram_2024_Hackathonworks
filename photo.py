from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration for file uploads
app.config['UPLOAD_FOLDER'] = 'static/uploads'  # Folder to save uploaded photos
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Rathana0037!',
    'database': 'student_db'
}

# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Route for the root URL - redirecting to the login page
@app.route('/')
def home():
    return redirect(url_for('login_page'))  # Redirects to the login page

# Route for displaying the login page (GET request)
@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

# Route for handling the login POST request
@app.route('/login', methods=['POST'])
def login():
    student_id = request.form['student_id']
    password = request.form['password']
    
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students WHERE student_id=%s AND dob=%s", (student_id, password))
    student = cursor.fetchone()
    conn.close()
    
    if student:
        return redirect(url_for('student_details', student_id=student['student_id']))
    else:
        return "Invalid credentials. Please try again."

# Route to show the student details
@app.route('/student_details/<int:student_id>')
def student_details(student_id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students WHERE student_id=%s", (student_id,))
    student = cursor.fetchone()
    conn.close()
    
    if student:
        return render_template('student_details.html', student=student)
    else:
        return "Student not found", 404

# Route to update student details
@app.route('/update/<int:student_id>', methods=['GET', 'POST'])
def update(student_id):
    if request.method == 'GET':
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students WHERE student_id=%s", (student_id,))
        student = cursor.fetchone()
        conn.close()
        
        if student:
            return render_template('edit_student.html', student=student)
        else:
            return "Student not found", 404

    elif request.method == 'POST':
        name = request.form['name']
        college_name = request.form['college_name']
        dob = request.form['dob']
        email = request.form['email']
        phone = request.form['phone']
        
        # Handle the photo upload
        photo = request.files.get('photo')
        photo_url = None
        
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            photo_url = f"uploads/{filename}"
        
        # Update the student's information in the database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE students 
            SET name=%s, college_name=%s, dob=%s, email=%s, phone=%s, photo_url=%s
            WHERE student_id=%s
        """, (name, college_name, dob, email, phone, photo_url, student_id))
        conn.commit()
        conn.close()
        
        return redirect(f'/student_details/{student_id}')

if __name__ == '__main__':
    app.run(debug=True)
