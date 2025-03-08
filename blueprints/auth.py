from flask import Blueprint, render_template, request, redirect, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

auth_bp = Blueprint('auth', __name__, template_folder='../templates')

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        contact = request.form['contact']
        password = request.form['password']
        gender = request.form['gender']
        password_hash = generate_password_hash(password)
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                'INSERT INTO users (name, email, contact, password_hash, gender) VALUES (?, ?, ?, ?, ?)', 
                (name, email, contact, password_hash, gender)
            )
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect('/auth/login')
        except sqlite3.IntegrityError:
            flash('Email already registered. Please use a different email.', 'error')
        finally:
            conn.close()
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
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
            session['username'] = user['name']
            session['role'] = user['role']
            flash('Login successful!', 'success')
            if user['role'] == 'admin':
                return redirect('/admin/analytics')
            else:
                return redirect('/profile')
        else:
            flash('Invalid email or password.', 'error')
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect('/')
