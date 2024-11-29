from flask import Flask, render_template, request, redirect
import mysql.connector

app = Flask(__name__)

# Database configuration
db_config = {
    'host': 'localhost',  # Database host
    'user': 'root',  # MySQL username
    'password': 'Rathana0037!',  # MySQL password
    'database': 'student_records'  # The name of the database/schema
}

# Route to the home page, where the login form is displayed
@app.route('/')
def home():
    return render_template('login.html')  # Login form page

# Route for handling the login
@app.route('/login', methods=['POST'])
def login():
    student_id = request.form['student_id']  # Get student ID from form input
    password = request.form['password']  # Get password (DOB) from form input
    
    # Connect to the database
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    # Query the database to check if the student exists with the provided ID and password (DOB)
    cursor.execute("SELECT * FROM students WHERE student_id=%s AND dob=%s", (student_id, password))
    student = cursor.fetchone()  # Fetch the first result (if any)
    conn.close()  # Close the database connection
    
    if student:
        return render_template('student_details.html', student=student)  # Display student details page if valid credentials
    else:
        return "Invalid credentials. Please try again."  # Show error if no matching record found

# Route to show the student details based on student_id
@app.route('/student_details/<int:student_id>')
def student_details(student_id):
    # Get the student's current details from the database based on student_id
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students WHERE student_id=%s", (student_id,))
    student = cursor.fetchone()  # Fetch the student's data
    conn.close()  # Close the database connection

    if student:
        return render_template('student_details.html', student=student)  # Render the student details page
    else:
        return "Student not found", 404  # If no student is found with the given ID, show error

# Route to update student details
@app.route('/update/<int:student_id>', methods=['GET', 'POST'])
def update(student_id):
    if request.method == 'GET':
        # Retrieve the current student details from the database when the form is opened for editing
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students WHERE student_id=%s", (student_id,))
        student = cursor.fetchone()  # Get the current details of the student
        conn.close()  # Close the database connection
        
        if student:
            return render_template('edit_student.html', student=student)  # Show the edit form with current student data
        else:
            return "Student not found", 404  # Return error if student ID is not found in the database

    elif request.method == 'POST':
        # Update student details when the form is submitted
        name = request.form['name']  # Get updated name from the form
        college_name = request.form['college_name']  # Get updated college name from the form
        dob = request.form['dob']  # Get updated DOB from the form
        email = request.form['email']  # Get updated email from the form
        phone = request.form['phone']  # Get updated phone number from the form
        
        # Connect to the database to update the student's information
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # Execute the update query to save the new values to the database
        cursor.execute("""
            UPDATE students 
            SET name=%s, college_name=%s, dob=%s, email=%s, phone=%s
            WHERE student_id=%s
        """, (name, college_name, dob, email, phone, student_id))
        conn.commit()  # Commit the changes to the database
        conn.close()  # Close the database connection
        
        # After updating, redirect to the student details page to display the updated information
        return redirect(f'/student_details/{student_id}')  # Redirect to show the updated student details

# Main driver for running the application
if __name__ == '__main__':
    app.run(debug=True)  # Run the Flask app in debug mode for easier development