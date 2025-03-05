from flask import Blueprint, render_template, redirect, flash, session, request
import sqlite3
from datetime import datetime

admin_bp = Blueprint('admin', __name__, template_folder='../templates')

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@admin_bp.route('/analytics')
def analytics():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Unauthorized access.', 'error')
        return redirect('/')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Daily scans grouped by date.
    cursor.execute('''
        SELECT DATE(upload_date) AS scan_date, COUNT(*) AS scans
        FROM documents
        GROUP BY scan_date
        ORDER BY scan_date DESC
    ''')
    daily_scans = cursor.fetchall()
    
    # Top users by scan count.
    cursor.execute('''
        SELECT name, COUNT(documents.id) AS scan_count 
        FROM users 
        LEFT JOIN documents ON users.id = documents.user_id 
        GROUP BY users.id 
        ORDER BY scan_count DESC
        LIMIT 5
    ''')
    top_users = cursor.fetchall()
    
    # Users with lowest credits.
    cursor.execute('''
        SELECT name, credits FROM users
        ORDER BY credits ASC
        LIMIT 5
    ''')
    low_credits = cursor.fetchall()
    
    conn.close()
    
    # Convert query results to list of dictionaries so they are JSON serializable.
    daily_scans = [dict(row) for row in daily_scans]
    top_users = [dict(row) for row in top_users]
    low_credits = [dict(row) for row in low_credits]
    
    # Calculate additional statistics.
    total_scans = sum(row['scans'] for row in daily_scans) if daily_scans else 0
    active_users = len([user for user in top_users if user['scan_count'] > 0])
    avg_similarity = 0  # Placeholder, update if you have data.
    
    return render_template('analytics.html', 
                           daily_scans=daily_scans, 
                           top_users=top_users, 
                           low_credits=low_credits,
                           total_scans=total_scans, 
                           active_users=active_users, 
                           avg_similarity=avg_similarity)

@admin_bp.route('/credits')
def admin_credit_requests():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Unauthorized access.', 'error')
        return redirect('/')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT credit_requests.id, users.name, credit_requests.requested_credits, credit_requests.status, credit_requests.request_date
        FROM credit_requests
        JOIN users ON credit_requests.user_id = users.id
        WHERE credit_requests.status = 'pending'
    ''')
    requests_list = cursor.fetchall()
    conn.close()
    return render_template('admin_credit_requests.html', requests=requests_list)

@admin_bp.route('/credits/approve/<int:req_id>', methods=['POST'])
def approve_credit_request(req_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Unauthorized access.', 'error')
        return redirect('/')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT user_id, requested_credits FROM credit_requests WHERE id = ? AND status = "pending"', 
        (req_id,)
    )
    req_data = cursor.fetchone()
    if req_data:
        user_id = req_data['user_id']
        requested_credits = req_data['requested_credits']
        cursor.execute(
            'UPDATE users SET credits = credits + ? WHERE id = ?', 
            (requested_credits, user_id)
        )
        cursor.execute(
            'UPDATE credit_requests SET status = "approved" WHERE id = ?', 
            (req_id,)
        )
        conn.commit()
        flash('Credit request approved.', 'success')
    else:
        flash('Credit request not found or already processed.', 'error')
    conn.close()
    return redirect('/admin/credits')


@admin_bp.route('/credits/deny/<int:req_id>', methods=['POST'])
def deny_credit_request(req_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Unauthorized access.', 'error')
        return redirect('/')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE credit_requests SET status = "denied" WHERE id = ? AND status = "pending"', 
        (req_id,)
    )
    conn.commit()
    conn.close()
    flash('Credit request denied.', 'info')
    return redirect('/admin/credits')
