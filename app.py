import os
from datetime import datetime
import sqlite3
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from werkzeug.security import generate_password_hash
from markupsafe import escape
from dotenv import load_dotenv
import atexit
import logging

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# Configure logging
logging.basicConfig(level=logging.INFO)

# Security headers configuration
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,  # Enable in production
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=3600  # 1 hour session timeout
)

# Database connection helper
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def initialize_database():
    with get_db_connection() as conn:
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
        conn.execute('''CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            content TEXT NOT NULL,
            upload_date DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS credit_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            requested_credits INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            request_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_type TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            details TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )''')
        
        # Seed a default admin account if one doesn't exist.
        admin_email = os.environ.get('ADMIN_EMAIL', 'akupadhyay810@gmail.com')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE role = 'admin'")
        admin = cursor.fetchone()
        if not admin:
            admin_password = os.environ.get('ADMIN_PASSWORD', '123')
            admin_password_hash = generate_password_hash(admin_password)
            # You can modify the name, contact, and gender as needed.
            cursor.execute(
                "INSERT INTO users (name, email, contact, password_hash, gender, role) VALUES (?, ?, ?, ?, ?, ?)",
                ('Site Administrator', admin_email, '8171090072', admin_password_hash, 'male', 'admin')
            )
            conn.commit()
            print("Default admin account created. Email:", admin_email)


def reset_daily_credits():
    with get_db_connection() as conn:
        today = datetime.now().date()
        conn.execute('''UPDATE users 
                      SET credits = CASE WHEN role = 'admin' THEN 9999 ELSE 20 END,
                          last_reset = ?
                      WHERE last_reset < ? OR last_reset IS NULL''',
                   (today, today))
        conn.commit()
    logging.info("Daily credits reset.")

# Custom Jinja filters
@app.template_filter('file_icon')
def file_icon_filter(filename):
    ext = filename.split('.')[-1].lower()
    icons = {
        'txt': '📄', 'csv': '📊', 'doc': '📑', 'docx': '📑', 'pdf': '📘'
    }
    return icons.get(ext, '📁')

@app.template_filter('datetimeformat')
def datetime_format(value, format='%b %d, %Y %H:%M'):
    if value is None:
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

# Register blueprints
from blueprints.auth import auth_bp
from blueprints.documents import doc_bp
from blueprints.admin import admin_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(doc_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')

@app.route('/')
def index():
    return app.jinja_env.get_template('index.html').render(current_year=datetime.now().year)

# Cleanup scheduler on exit
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    initialize_database()
    app.run(ssl_context='adhoc' if os.environ.get('FLASK_ENV') == 'production' else None)
