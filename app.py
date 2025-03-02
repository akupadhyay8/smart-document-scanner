import os
from flask import Flask, render_template, request, redirect, session, flash, Response
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import sqlite3
from Levenshtein import distance as levenshtein_distance

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Replace with a strong secret key

# Allowed file extensions and upload folder
ALLOWED_EXTENSIONS = {'txt', 'csv'}
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize the database schema with updated user fields
def initialize_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            contact TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            credits INTEGER DEFAULT 20,
            last_reset DATE DEFAULT CURRENT_DATE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            content TEXT NOT NULL,
            upload_date DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS credit_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            requested_credits INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

# Improved daily credits reset (should be scheduled to run at midnight in production)
def reset_daily_credits():
    conn = get_db_connection()
    cursor = conn.cursor()
    today = datetime.now().date()
    cursor.execute(
        'UPDATE users SET credits = 20, last_reset = ? WHERE last_reset < ?', 
        (today, today)
    )
    conn.commit()
    conn.close()

# Check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Homepage
@app.route('/')
def index():
    return render_template('index.html')

# User Registration - now uses Name, Email, Contact, and Password
@app.route('/auth/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        contact = request.form['contact']
        password = request.form['password']
        password_hash = generate_password_hash(password)
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO users (name, email, contact, password_hash) VALUES (?, ?, ?, ?)', 
                (name, email, contact, password_hash)
            )
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect('/auth/login')
        except sqlite3.IntegrityError:
            flash('Email already registered. Please use a different email.', 'error')
        finally:
            conn.close()
    return render_template('register.html')

# User Login - now uses Email (as the user ID) and Password
@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['name']  # using name for display
            session['role'] = user['role']
            flash('Login successful!', 'success')
            return redirect('/user/profile')
        else:
            flash('User ID or password not found.', 'error')
    return render_template('login.html')


# User Profile with export report bonus link
@app.route('/user/profile')
def profile():
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'error')
        return redirect('/auth/login')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    cursor.execute('SELECT * FROM documents WHERE user_id = ?', (session['user_id'],))
    documents = cursor.fetchall()
    conn.close()
    return render_template('profile.html', user=user, documents=documents)

# Document Upload: Save file locally and in the database, then deduct one credit
@app.route('/scan', methods=['GET', 'POST'])
def upload_document():
    if 'user_id' not in session:
        flash('Please log in to upload documents.', 'error')
        return redirect('/auth/login')
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded.', 'error')
            return redirect('/scan')
        file = request.files['file']
        if file.filename == '':
            flash('No file selected.', 'error')
            return redirect('/scan')
        if not allowed_file(file.filename):
            flash('Only TXT or CSV files are allowed.', 'error')
            return redirect('/scan')

        file_content = file.read()
        try:
            content = file_content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                content = file_content.decode('latin-1')
            except UnicodeDecodeError:
                flash('Unsupported file encoding. Please upload a valid text file.', 'error')
                return redirect('/scan')
        # Save file locally
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        with open(filepath, 'wb') as f:
            f.write(file_content)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT credits FROM users WHERE id = ?', (session['user_id'],))
        user_credits = cursor.fetchone()['credits']
        if user_credits < 1:
            flash('Insufficient credits. Please request more.', 'error')
            return redirect('/user/profile')
        cursor.execute(
            'INSERT INTO documents (user_id, filename, content) VALUES (?, ?, ?)', 
            (session['user_id'], filename, content)
        )
        cursor.execute('UPDATE users SET credits = credits - 1 WHERE id = ?', (session['user_id'],))
        conn.commit()
        conn.close()
        flash('Document uploaded successfully!', 'success')
        return redirect('/user/profile')
    return render_template('upload.html')

# Document Matching using Levenshtein distance
@app.route('/matches/<int:doc_id>')
def get_matches(doc_id):
    if 'user_id' not in session:
        flash('Please log in to view matches.', 'error')
        return redirect('/auth/login')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT content FROM documents WHERE id = ?', (doc_id,))
    target_row = cursor.fetchone()
    if not target_row:
        flash('Document not found.', 'error')
        conn.close()
        return redirect('/user/profile')
    target_content = target_row['content']
    cursor.execute('SELECT * FROM documents WHERE user_id = ? AND id != ?', (session['user_id'], doc_id))
    documents = cursor.fetchall()
    conn.close()
    matches = []
    for doc in documents:
        similarity = levenshtein_distance(target_content, doc['content'])
        # Adjust the threshold as needed for your document lengths
        if similarity < 10:
            matches.append(doc)
    return render_template('matches.html', matches=matches)

# Export Scan History (Bonus Feature)
@app.route('/user/export')
def export_report():
    if 'user_id' not in session:
        flash('Please log in to export your report.', 'error')
        return redirect('/auth/login')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT filename, upload_date FROM documents WHERE user_id = ?', (session['user_id'],))
    documents = cursor.fetchall()
    conn.close()
    report = "Your Scan History:\n\n"
    for doc in documents:
        report += f"Filename: {doc['filename']} - Uploaded on: {doc['upload_date']}\n"
    return Response(report, mimetype='text/plain', headers={"Content-Disposition": "attachment;filename=scan_history.txt"})

# Credit Request endpoint for regular users
@app.route('/credits/request', methods=['GET', 'POST'])
def credit_request():
    if 'user_id' not in session:
        flash('Please log in to request credits.', 'error')
        return redirect('/auth/login')
    if request.method == 'POST':
        try:
            requested_credits = int(request.form['requested_credits'])
            if requested_credits <= 0:
                flash('Please request a positive number of credits.', 'error')
                return redirect('/credits/request')
        except ValueError:
            flash('Invalid number.', 'error')
            return redirect('/credits/request')
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO credit_requests (user_id, requested_credits) VALUES (?, ?)', 
            (session['user_id'], requested_credits)
        )
        conn.commit()
        conn.close()
        flash('Credit request submitted successfully.', 'success')
        return redirect('/user/profile')
    return render_template('credit_request.html')

# Admin view of pending credit requests
@app.route('/admin/credits')
def admin_credit_requests():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Unauthorized access.', 'error')
        return redirect('/')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT credit_requests.id, users.name, credit_requests.requested_credits, credit_requests.status
        FROM credit_requests
        JOIN users ON credit_requests.user_id = users.id
        WHERE credit_requests.status = 'pending'
    ''')
    requests_list = cursor.fetchall()
    conn.close()
    return render_template('admin_credit_requests.html', requests=requests_list)

# Admin endpoint to approve a credit request
@app.route('/admin/credits/approve/<int:req_id>', methods=['POST'])
def approve_credit_request(req_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Unauthorized access.', 'error')
        return redirect('/')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, requested_credits FROM credit_requests WHERE id = ? AND status = "pending"', (req_id,))
    req_data = cursor.fetchone()
    if req_data:
        user_id = req_data['user_id']
        requested_credits = req_data['requested_credits']
        cursor.execute('UPDATE users SET credits = credits + ? WHERE id = ?', (requested_credits, user_id))
        cursor.execute('UPDATE credit_requests SET status = "approved" WHERE id = ?', (req_id,))
        conn.commit()
        flash('Credit request approved.', 'success')
    else:
        flash('Credit request not found or already processed.', 'error')
    conn.close()
    return redirect('/admin/credits')

# Admin endpoint to deny a credit request
@app.route('/admin/credits/deny/<int:req_id>', methods=['POST'])
def deny_credit_request(req_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Unauthorized access.', 'error')
        return redirect('/')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE credit_requests SET status = "denied" WHERE id = ? AND status = "pending"', (req_id,))
    conn.commit()
    conn.close()
    flash('Credit request denied.', 'info')
    return redirect('/admin/credits')

# Admin Analytics Dashboard
@app.route('/admin/analytics')
def analytics():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Unauthorized access.', 'error')
        return redirect('/')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT name, COUNT(documents.id) as scan_count 
        FROM users 
        LEFT JOIN documents ON users.id = documents.user_id 
        GROUP BY users.id
        ORDER BY scan_count DESC
    ''')
    top_users = cursor.fetchall()
    cursor.execute('SELECT name, credits FROM users')
    credit_usage = cursor.fetchall()
    conn.close()
    return render_template('analytics.html', top_users=top_users, credit_usage=credit_usage)

# Logout
@app.route('/auth/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect('/')

if __name__ == '__main__':
    initialize_database()
    reset_daily_credits()  # For production, schedule this to run daily at midnight.
    app.run(debug=True)
