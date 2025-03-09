import os
import sqlite3
import string
from collections import Counter
from datetime import datetime
import difflib
from flask import Blueprint, render_template, flash, session, redirect, request

# Create an admin blueprint to keep all admin-related routes together.
admin_bp = Blueprint('admin', __name__, template_folder='../templates')

# Helper Functions

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_common_topics():
    """Extract the top 10 most common words from scanned document contents."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM documents")
    docs = cursor.fetchall()
    conn.close()
    
    # Merge all document content into one large string
    all_text = " ".join([doc["content"] for doc in docs])
    all_text = all_text.lower()
    translator = str.maketrans("", "", string.punctuation)
    all_text = all_text.translate(translator)
    words = all_text.split()

    # Define words to ignore
    stopwords = {"the", "and", "is", "in", "to", "of", "a", "an", "for", "with", "on", "at", "by", "this", "that", "it", "as", "are", "from"}
    filtered_words = [w for w in words if w not in stopwords]
    common_topics = Counter(filtered_words).most_common(10)
    return common_topics

def get_daily_scans_by_user():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.name as user_name, DATE(d.upload_date) as scan_date, COUNT(*) as scans
        FROM documents d
        JOIN users u ON d.user_id = u.id
        WHERE u.role = 'user'
        GROUP BY d.user_id, scan_date
        ORDER BY scan_date
    ''')
    data = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return data

# Main Analytics Route for Admin Dashboard

@admin_bp.route('/analytics')
def analytics():
     # Ensure only admin users can access the analytics dashboard.

    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Unauthorized access.', 'error')
        return redirect('/')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Retrieve daily scan data for the line chart.
    cursor.execute('''
        SELECT DATE(upload_date) AS scan_date, COUNT(*) AS scans
        FROM documents
        GROUP BY scan_date
        ORDER BY scan_date DESC
    ''')
    daily_scans = [dict(row) for row in cursor.fetchall()]
    
    # Also get daily scans per user (if needed for another chart).
    daily_scans_by_user = get_daily_scans_by_user()
    
    # 2. Get top 5 users by the number of scans.
    cursor.execute('''
        SELECT name, COUNT(documents.id) AS scan_count 
        FROM users 
        LEFT JOIN documents ON users.id = documents.user_id 
        WHERE users.role = 'user'
        GROUP BY users.id 
        ORDER BY scan_count DESC
        LIMIT 5
    ''')
    top_users = [dict(row) for row in cursor.fetchall()]
    
    # 3. Get 5 users with the lowest credits (for display in a table).
    cursor.execute('''
        SELECT name, credits FROM users
        WHERE role = 'user'
        ORDER BY credits ASC
        LIMIT 5
    ''')
    low_credits = [dict(row) for row in cursor.fetchall()]
    
    # 4. Calculate "credits used" as the total number of scans per user.
    cursor.execute('''
        SELECT u.name, COUNT(d.id) AS credit_used
        FROM users u
        LEFT JOIN documents d ON u.id = d.user_id
        WHERE u.role = 'user'
        GROUP BY u.id
        ORDER BY credit_used DESC
    ''')
    credit_usage = [dict(row) for row in cursor.fetchall()]
    
    # 5. Compute match statistics for a pie chart.
    cursor.execute('SELECT id, content FROM documents WHERE user_id IN (SELECT id FROM users WHERE role="user")')
    docs = cursor.fetchall()
    successful = 0
    unsuccessful = 0
    threshold = 0.7  # similarity threshold
    docs_list = list(docs)
    for i in range(len(docs_list)):
        matched = False
        for j in range(len(docs_list)):
            if i == j:
                continue
            sim = difflib.SequenceMatcher(None, docs_list[i]['content'], docs_list[j]['content']).ratio()
            if sim >= threshold:
                matched = True
                break
        if matched:
            successful += 1
        else:
            unsuccessful += 1
    match_stats = {'successful': successful, 'unsuccessful': unsuccessful}
    
    # 6. Calculate an average similarity metric for additional display.
    cursor.execute('SELECT content FROM documents WHERE user_id IN (SELECT id FROM users WHERE role="user")')
    all_docs = [row['content'] for row in cursor.fetchall()]
    total_similarity = 0
    pair_count = 0
    if len(all_docs) >= 2:
        for i in range(len(all_docs)):
            for j in range(i+1, len(all_docs)):
                total_similarity += difflib.SequenceMatcher(None, all_docs[i], all_docs[j]).ratio()
                pair_count += 1
        avg_similarity = total_similarity / pair_count if pair_count > 0 else 0
    else:
        avg_similarity = None

    conn.close()
    
    # Calculate some aggregate stats.
    total_scans = sum(row['scans'] for row in daily_scans) if daily_scans else 0
    active_users = len([u for u in top_users if u['scan_count'] > 0])
    avg_match_display = f"{round(avg_similarity*100,1)}%" if avg_similarity is not None else "N/A"
    common_topics = get_common_topics()
    
    # Render the analytics dashboard template with all the collected data.
    return render_template('analytics.html', 
                           daily_scans=daily_scans, 
                           daily_scans_by_user=daily_scans_by_user,
                           top_users=top_users, 
                           low_credits=low_credits,
                           credit_usage=credit_usage,
                           match_stats=match_stats,
                           total_scans=total_scans, 
                           active_users=active_users, 
                           avg_similarity=avg_match_display,
                           common_topics=common_topics)

# --- Admin Credit Request Endpoints ---

@admin_bp.route('/credits/approve/<int:request_id>', methods=['POST'])
def approve_credit_request(request_id):

    # Only admins should be able to approve credit requests.
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Unauthorized access.', 'error')
        return redirect('/')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM credit_requests WHERE id = ?", (request_id,))
    credit_request = cursor.fetchone()
    if credit_request:

        # Mark the request as approved and add the requested credits to the user.
        cursor.execute("UPDATE credit_requests SET status = 'approved' WHERE id = ?", (request_id,))
        cursor.execute("UPDATE users SET credits = credits + ? WHERE id = ?", 
                       (credit_request['requested_credits'], credit_request['user_id']))
        conn.commit()
        flash('Credit request approved.', 'success')
    else:
        flash('Credit request not found.', 'error')
    conn.close()
    return redirect('/admin/credits')

@admin_bp.route('/credits/deny/<int:request_id>', methods=['POST'])
def deny_credit_request(request_id):

    # Only admins should be able to deny credit requests.
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Unauthorized access.', 'error')
        return redirect('/')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM credit_requests WHERE id = ?", (request_id,))
    credit_request = cursor.fetchone()
    if credit_request:
        # Mark the request as denied.
        cursor.execute("UPDATE credit_requests SET status = 'denied' WHERE id = ?", (request_id,))
        conn.commit()
        flash('Credit request denied.', 'success')
    else:
        flash('Credit request not found.', 'error')
    conn.close()
    return redirect('/admin/credits')

@admin_bp.route('/credits')
def manage_credit_requests():
    # Admin view for managing pending credit requests.
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Unauthorized access.', 'error')
        return redirect('/')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT cr.*, u.name 
        FROM credit_requests cr
        JOIN users u ON cr.user_id = u.id
        WHERE cr.status = 'pending'
        ORDER BY cr.request_date DESC
    ''')
    requests = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return render_template('admin_credit_requests.html', requests=requests)

@admin_bp.route('/users')
def view_all_users():
    # Admin view to see all users.
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Unauthorized access.', 'error')
        return redirect('/')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    return render_template('admin_all_users.html', users=users)


@admin_bp.route('/user/<int:user_id>', methods=['GET', 'POST'])
def admin_user_details(user_id):
    # Admin view to see details of a specific user and update credits.
    if 'user_id' not in session or session.get('role') != 'admin':
        flash('Unauthorized access.', 'error')
        return redirect('/')
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == 'POST':
        try:
            new_credits = int(request.form['credits'])
            cursor.execute("UPDATE users SET credits = ? WHERE id = ?", (new_credits, user_id))
            conn.commit()
            flash('User credits updated.', 'success')
        except ValueError:
            flash('Invalid input for credits.', 'error')
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return render_template('admin_user_details.html', user=user)
