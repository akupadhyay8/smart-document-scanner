from flask import Blueprint, render_template, redirect, flash, session, request
import sqlite3

admin_bp = Blueprint('admin', __name__, template_folder='../templates')

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

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

@admin_bp.route('/credits/deny/<int:req_id>', methods=['POST'])
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

@admin_bp.route('/analytics')
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
    # Calculate total scans and active users
    total_scans = sum(user['scan_count'] for user in top_users)
    active_users = len([user for user in top_users if user['scan_count'] > 0])
    avg_similarity = 75  # Placeholder value; compute if data available.
    cursor.execute('SELECT name, credits FROM users')
    credit_usage = cursor.fetchall()
    conn.close()
    return render_template('analytics.html', top_users=top_users, credit_usage=credit_usage,
                           total_scans=total_scans, active_users=active_users, avg_similarity=avg_similarity)
