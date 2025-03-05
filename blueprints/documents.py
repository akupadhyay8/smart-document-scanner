from flask import Blueprint, render_template, request, redirect, flash, session, Response
import os
import sqlite3
import difflib
import re
from werkzeug.utils import secure_filename
from datetime import datetime
from Levenshtein import distance as levenshtein_distance

doc_bp = Blueprint('documents', __name__, template_folder='../templates')
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'csv'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@doc_bp.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Please log in to access your profile.', 'error')
        return redirect('/auth/login')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    cursor.execute('SELECT * FROM documents WHERE user_id = ? ORDER BY upload_date DESC', (session['user_id'],))
    documents = cursor.fetchall()
    cursor.execute('SELECT * FROM credit_requests WHERE user_id = ? ORDER BY request_date DESC', (session['user_id'],))
    credit_requests = cursor.fetchall()
    conn.close()
    return render_template('profile.html', user=user, documents=documents, credit_requests=credit_requests)


@doc_bp.route('/scan', methods=['GET', 'POST'])
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
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        with open(filepath, 'wb') as f:
            f.write(file_content)
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # If user is NOT admin, check if they have credits.
        if session.get('role') != 'admin':
            cursor.execute('SELECT credits FROM users WHERE id = ?', (session['user_id'],))
            user_credits = cursor.fetchone()['credits']
            if user_credits < 1:
                flash('Insufficient credits. Please request more.', 'error')
                conn.close()
                return redirect('/profile')
        
        # Insert the document.
        cursor.execute('INSERT INTO documents (user_id, filename, content) VALUES (?, ?, ?)', 
                       (session['user_id'], filename, content))
        
        # Deduct a credit if the user is not an admin.
        if session.get('role') != 'admin':
            cursor.execute('UPDATE users SET credits = credits - 1 WHERE id = ?', (session['user_id'],))
        
        conn.commit()
        conn.close()
        flash('Document uploaded successfully!', 'success')
        return redirect('/profile')
    
    # For GET requests, fetch the user to pass into the template.
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    return render_template('upload.html', user=user)

@doc_bp.route('/matches/<int:doc_id>')
def get_matches(doc_id):
    if 'user_id' not in session:
        flash('Please log in to view matches.', 'error')
        return redirect('/auth/login')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT content, filename FROM documents WHERE id = ?', (doc_id,))
    target_row = cursor.fetchone()
    if not target_row:
        flash('Document not found.', 'error')
        conn.close()
        return redirect('/profile')
    target_content = target_row['content']
    target_filename = target_row['filename']
    
    cursor.execute('SELECT * FROM documents WHERE user_id = ? AND id != ?', (session['user_id'], doc_id))
    documents = cursor.fetchall()
    conn.close()
    
    matches = []
    for doc in documents:
        # Use difflib to calculate a similarity ratio.
        similarity_ratio = difflib.SequenceMatcher(None, target_content, doc['content']).ratio()
        if similarity_ratio > 0.1:  # Only consider documents with at least 10% similarity.
            match = dict(doc)
            match['similarity'] = similarity_ratio
            matches.append(match)
    
    # Sort matches descending by similarity.
    matches = sorted(matches, key=lambda x: x['similarity'], reverse=True)
    
    # Pass target_doc_id to the template for comparison links.
    return render_template('matches.html', matches=matches, target_doc_id=doc_id, target_filename=target_filename)

@doc_bp.route('/user/export')
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

@doc_bp.route('/credits/request', methods=['GET', 'POST'])
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
        cursor.execute('INSERT INTO credit_requests (user_id, requested_credits) VALUES (?, ?)', 
                       (session['user_id'], requested_credits))
        conn.commit()
        conn.close()
        flash('Credit request submitted successfully.', 'success')
        return redirect('/profile')
    
    # For GET requests, fetch the user to pass into the template.
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    return render_template('credit_request.html', user=user)


@doc_bp.route('/compare/<int:doc_id>/<int:match_id>')
def compare_docs(doc_id, match_id):
    if 'user_id' not in session:
        flash('Please log in to compare documents.', 'error')
        return redirect('/auth/login')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT filename, content FROM documents WHERE id = ?', (doc_id,))
    doc1 = cursor.fetchone()
    cursor.execute('SELECT filename, content FROM documents WHERE id = ?', (match_id,))
    doc2 = cursor.fetchone()
    conn.close()
    
    if not doc1 or not doc2:
        flash('One of the documents was not found.', 'error')
        return redirect('/profile')
    
    # Split the content into lines and filter out empty lines.
    lines1 = [line for line in doc1['content'].splitlines() if line.strip() != ""]
    lines2 = [line for line in doc2['content'].splitlines() if line.strip() != ""]
    
    # Generate an HTML diff using difflib.HtmlDiff.
    html_diff = difflib.HtmlDiff().make_table(
        lines1,
        lines2,
        fromdesc=f"From: {doc1['filename']} (F)",
        todesc=f"To: {doc2['filename']} (T)",
        context=True,
        numlines=2
    )
    
    return render_template('compare.html', diff_html=html_diff)
