import os
from datetime import datetime
import sqlite3
from flask import Flask, render_template
from apscheduler.schedulers.background import BackgroundScheduler
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
import atexit
import logging

# Load environment variables from a .env file. This helps keep sensitive info safe.
load_dotenv()

# Create the Flask application instance.
app = Flask(__name__)

# Set the secret key for sessions. If not provided in the environment, generate a random one.
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# Logging & Security Configuration
# Configure logging
logging.basicConfig(level=logging.INFO)

# Security headers configuration
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=3600  # 1 hour session timeout
)

# Database Functions & Initialization
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def initialize_database():
    with get_db_connection() as conn:
        # Users table holds user details and their roles/credits.
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            contact TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            gender TEXT DEFAULT 'others',
            role TEXT DEFAULT 'user',
            credits INTEGER DEFAULT 20,
            last_reset DATE DEFAULT CURRENT_DATE
        )''')
        # Documents table holds scanned documents and their details.
        conn.execute('''CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            original_filename TEXT,
            content TEXT NOT NULL,
            upload_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )''')
        # Credit requests table for tracking additional credit requests by users.
        conn.execute('''CREATE TABLE IF NOT EXISTS credit_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            requested_credits INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            request_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )''')
        # Activity logs table to track user activities (optional but useful).
        conn.execute('''CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_type TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            details TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )''')
        
        # Seeded a default admin account
        admin_email = os.environ.get('ADMIN_EMAIL', 'akupadhyay810@gmail.com')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE role = 'admin'")
        admin = cursor.fetchone()
        if not admin:
            admin_password = os.environ.get('ADMIN_PASSWORD', '123')
            admin_password_hash = generate_password_hash(admin_password)
            cursor.execute(
                "INSERT INTO users (name, email, contact, password_hash, gender, role, credits) VALUES (?, ?, ?, ?, ?, ?, ?)",
                ('Site Administrator', admin_email, '8171090072', admin_password_hash, 'male', 'admin', 9999)
            )
            conn.commit()
            logging.info("Default admin account created. Email: %s", admin_email)

# Scheduled Tasks
def reset_daily_credits():
    with get_db_connection() as conn:
        today = datetime.now().date()
        conn.execute('''UPDATE users 
                        SET credits = CASE WHEN role = 'admin' THEN 9999 ELSE 20 END,
                            last_reset = ?
                        WHERE last_reset < ? OR last_reset IS NULL''',
                     (today, today))
        conn.commit()
    logging.info("Daily credits reset on %s.", today)

# Custom Jinja filters
@app.template_filter('file_icon')
def file_icon_filter(filename):
    ext = filename.split('.')[-1].lower()
    icons = {
        'txt': '📄', 'csv': '📊'
    }
    return icons.get(ext, '📁')

@app.template_filter('datetimeformat')
def datetime_format(value, format='%b %d, %Y %H:%M'):
    if not value:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except Exception:
            return value
    return value.strftime(format)

@app.template_filter('pluralize')
def pluralize(number, singular='', plural='s'):
    return singular if number == 1 else plural

# Security headers middleware
@app.after_request
def add_security_headers(response):
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://fonts.gstatic.com"
    return response

# Scheduler configuration for daily credit reset
scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(
    func=reset_daily_credits,
    trigger='cron',
    hour=0,
    minute=0,
    timezone='UTC'
)
scheduler.start()

# Blueprint Registration & Routes
from blueprints.auth import auth_bp
from blueprints.documents import doc_bp
from blueprints.admin import admin_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(doc_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')

@app.route('/')
def index():
    return render_template('index.html', current_year=datetime.now().year)

# Cleanup scheduler on exit and shutdown.
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    # Initialize the database tables and seed the admin account if needed.
    initialize_database()
    # Run the app. Use an ad-hoc SSL context for production
    app.run(ssl_context='adhoc' if os.environ.get('FLASK_ENV') == 'production' else None)
