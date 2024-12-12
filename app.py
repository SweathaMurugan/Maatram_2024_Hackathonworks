from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import os
import uuid
from datetime import timedelta

app = Flask(__name__)

# Configuration
app.config['MONGO_URI'] = os.getenv('MONGO_URI', "mongodb+srv://projectpro2000jan1:hackathon2024@studentdb.jrm0m.mongodb.net/studentdb?retryWrites=true&w=majority")
app.secret_key = os.getenv('SECRET_KEY', "your_secret_key")
mongo = PyMongo(app)

# Ensure static directory for uploaded certificates exists
CERTIFICATE_DIR = os.path.join(app.root_path, 'static', 'certificates')
if not os.path.exists(CERTIFICATE_DIR):
    os.makedirs(CERTIFICATE_DIR)

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'png'}

# Session timeout
app.permanent_session_lifetime = timedelta(minutes=30)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def role_required(role):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session['role'] != role:
                flash("Unauthorized access", "error")
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'Student')

        if not (name and email and password):
            flash("All fields are required", "error")
            return redirect(url_for('register'))

        if mongo.db.students.find_one({'email': email}):
            flash('Email already registered', 'error')
            return redirect(url_for('login'))

        hashed_password = generate_password_hash(password)
        new_user = {
            'name': name,
            'email': email,
            'password': hashed_password,
            'role': role
        }

        try:
            mongo.db.students.insert_one(new_user)
            flash('Registration successful', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Error during registration: {e}", 'error')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not (email and password):
            flash("Email and Password are required", "error")
            return redirect(url_for('login'))

        user = mongo.db.students.find_one({'email': email})
        if not user or not check_password_hash(user['password'], password):
            flash('Invalid credentials', 'error')
            return redirect(url_for('login'))

        session['user_id'] = str(user['_id'])
        session['role'] = user['role']
        session.permanent = True
        print(f"Session set: user_id={session['user_id']}, role={session['role']}")
        flash('Login successful!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    role = session.get('role')
    if role == 'Admin':
        meetings = list(mongo.db.meetings.find())
        return render_template('admin_dashboard.html', meetings=meetings)
    elif role == 'Student':
        certificates = list(mongo.db.certificates.find({'student_id': session['user_id']}))
        return render_template('student_dashboard.html', certificates=certificates)
    return redirect(url_for('login'))

@app.route('/create_meeting', methods=['GET', 'POST'])
@role_required('Admin')
def create_meeting():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        date = request.form.get('date')

        if not (title and description and date):
            flash('All fields are required', 'error')
            return redirect(url_for('create_meeting'))

        new_meeting = {
            'title': title,
            'description': description,
            'date': date
        }
        mongo.db.meetings.insert_one(new_meeting)
        flash('Meeting created successfully', 'success')
        return redirect(url_for('dashboard'))
    return render_template('create_meeting.html')

@app.route('/upload_certificate', methods=['GET', 'POST'])
@role_required('Student')
def upload_certificate():
    if request.method == 'POST':
        file = request.files.get('certificate')
        if file and allowed_file(file.filename):
            unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
            file_path = os.path.join(CERTIFICATE_DIR, unique_filename)
            file.save(file_path)

            new_certificate = {
                'student_id': session['user_id'],
                'file_path': f"certificates/{unique_filename}"
            }
            mongo.db.certificates.insert_one(new_certificate)
            flash('Certificate uploaded successfully', 'success')
        else:
            flash('Invalid file type', 'error')
        return redirect(url_for('dashboard'))
    return render_template('upload_certificate.html')

@app.route('/delete_certificate/<string:cert_id>')
@role_required('Student')
def delete_certificate(cert_id):
    certificate = mongo.db.certificates.find_one({'_id': ObjectId(cert_id)})
    if certificate and certificate['student_id'] == session['user_id']:
        try:
            mongo.db.certificates.delete_one({'_id': ObjectId(cert_id)})
            flash('Certificate deleted successfully', 'success')
        except Exception as e:
            flash(f"Error deleting certificate: {e}", 'error')
    else:
        flash('Unauthorized action', 'error')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
