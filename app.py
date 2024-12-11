from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['MONGO_URI'] = "mongodb+srv://projectpro2000jan1:hackathon2024@studentdb.jrm0m.mongodb.net/yourdatabase?retryWrites=true&w=majority"
app.secret_key = "your_secret_key"
mongo = PyMongo(app)

# Ensure static directory for uploaded certificates exists
CERTIFICATE_DIR = os.path.join('static', 'certificates')
if not os.path.exists(CERTIFICATE_DIR):
    os.makedirs(CERTIFICATE_DIR)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']

        if mongo.db.students.find_one({'email': email}):
            flash('Email already registered', 'error')
            return redirect(url_for('signup'))

        new_user = {
            'name': name,
            'email': email,
            'password': password,
            'role': role
        }
        mongo.db.students.insert_one(new_user)
        flash('Signup successful', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = mongo.db.students.find_one({'email': email})

        if not user or not check_password_hash(user['password'], password):
            flash('Invalid credentials', 'error')
            return redirect(url_for('login'))

        session['user_id'] = str(user['_id'])
        session['role'] = user['role']
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
def create_meeting():
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        date = request.form['date']

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
def upload_certificate():
    if 'role' not in session or session['role'] != 'Student':
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files['certificate']
        if file:
            filename = f"certificates/{file.filename}"
            file.save(os.path.join('static', filename))

            new_certificate = {
                'student_id': session['user_id'],
                'file_path': filename
            }
            mongo.db.certificates.insert_one(new_certificate)
            flash('Certificate uploaded successfully', 'success')
            return redirect(url_for('dashboard'))
    return render_template('upload_certificate.html')

@app.route('/delete_certificate/<string:cert_id>')
def delete_certificate(cert_id):
    if 'role' not in session or session['role'] != 'Student':
        return redirect(url_for('login'))

    certificate = mongo.db.certificates.find_one({'_id': ObjectId(cert_id)})
    if certificate and certificate['student_id'] == session['user_id']:
        mongo.db.certificates.delete_one({'_id': ObjectId(cert_id)})
        flash('Certificate deleted successfully', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
