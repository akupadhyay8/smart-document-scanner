from flask import Flask, render_template, request, redirect, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import sqlite3
from Levenshtein import distance as levenshtein_distance

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for session management

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'csv'}

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize the database schema
def initialize_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
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

# Reset daily credits at midnight
def reset_daily_credits():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET credits = 20 WHERE last_reset < ?', (datetime.now().date(),))
    cursor.execute('UPDATE users SET last_reset = ?', (datetime.now().date(),))
    conn.commit()
    conn.close()

# Check if file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Homepage
@app.route('/')
def index():
    return render_template('index.html')

# User Registration
@app.route('/auth/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_hash = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect('/auth/login')
        except sqlite3.IntegrityError:
            flash('Username already exists. Please choose another.', 'error')
        finally:
            conn.close()
    return render_template('register.html')

# User Login
@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash('Login successful!', 'success')
            return redirect('/user/profile')
        else:
            flash('Invalid username or password.', 'error')
    return render_template('login.html')

# User Profile
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

# Document Upload
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

        try:
            content = file.read().decode('utf-8')
        except UnicodeDecodeError:
            try:
                content = file.read().decode('latin-1')  # Try a different encoding
            except UnicodeDecodeError:
                flash('Unsupported file encoding. Please upload a valid UTF-8 text file.', 'error')
                return redirect('/scan')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT credits FROM users WHERE id = ?', (session['user_id'],))
        user_credits = cursor.fetchone()['credits']

        if user_credits < 1:
            flash('Insufficient credits. Please request more.', 'error')
            return redirect('/user/profile')

        cursor.execute('INSERT INTO documents (user_id, filename, content) VALUES (?, ?, ?)', 
                       (session['user_id'], file.filename, content))
        cursor.execute('UPDATE users SET credits = credits - 1 WHERE id = ?', (session['user_id'],))
        conn.commit()
        conn.close()

        flash('Document uploaded successfully!', 'success')
        return redirect('/user/profile')

    return render_template('upload.html')

# Document Matching
@app.route('/matches/<int:doc_id>')
def get_matches(doc_id):
    if 'user_id' not in session:
        flash('Please log in to view matches.', 'error')
        return redirect('/auth/login')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT content FROM documents WHERE id = ?', (doc_id,))
    target_content = cursor.fetchone()['content']

    cursor.execute('SELECT * FROM documents WHERE user_id = ? AND id != ?', (session['user_id'], doc_id))
    documents = cursor.fetchall()
    conn.close()

    matches = []
    for doc in documents:
        similarity = levenshtein_distance(target_content, doc['content'])
        if similarity < 10:  # Adjust threshold as needed
            matches.append(doc)

    return render_template('matches.html', matches=matches)

# Admin Analytics
@app.route('/admin/analytics')
def analytics():
    if 'user_id' not in session or session['role'] != 'admin':
        flash('Unauthorized access.', 'error')
        return redirect('/')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT username, COUNT(documents.id) as scan_count FROM users LEFT JOIN documents ON users.id = documents.user_id GROUP BY users.id ORDER BY scan_count DESC')
    top_users = cursor.fetchall()

    cursor.execute('SELECT username, credits FROM users')
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
    reset_daily_credits()
    app.run(debug=True)