# DocScan Pro

**DocScan Pro** is a self-contained document scanning and matching system featuring a built-in credit system. Each user receives 20 free scans per day, and additional scans can be requested via a credit request system. The project also includes an analytics dashboard for administrators to view scan statistics, match statistics, and user credit usage.

## Features

- **User Management & Authentication**  
  - User registration and login with role-based access (Regular Users and Admins).
  - Profile dashboard displaying scan history and credit balance.

- **Credit System**  
  - 20 free scans per day (auto-reset at midnight).
  - Option for users to request additional credits.
  - Admin approval/denial for credit requests.
  - Scans deduct one credit from the user's balance.

- **Document Scanning & Matching**  
  - Upload plain text (`.txt`) and CSV files.
  - Documents are stored locally.
  - Basic text matching to identify similar documents.
  - integration of AI-powered matching using pre-trained models (via SentenceTransformer).

- **Analytics Dashboard (Admin)**  
  - Interactive line chart showing daily scans.
  - Pie chart displaying match statistics (successful vs. unsuccessful matches).
  - Bar chart showing scans performed by each user (credit usage independent of manual changes).
  - Tables for top users by scan count and users with lowest credits.

- **Additional Features**  
  - Automated daily credit reset using APScheduler.
  - User activity logs.
  - Export scan history as a text file.
  - Responsive and professional UI using HTML, CSS, and vanilla JavaScript.

## Tech Stack

- **Frontend:**  
  - HTML, CSS, JavaScript (vanilla)
  - Chart.js for data visualization

- **Backend:**  
  - Python 3.x with Flask  
  - APScheduler for scheduling tasks  
  - SQLite for the database  
  - Custom text matching using difflib (and optional AI-powered matching using SentenceTransformer)

- **Other Libraries:**  
  - python-dotenv for environment variable management  
  - Werkzeug for secure password hashing

## Directory Structure

Document_Scanner/
 ├── app.py
 ├── blueprints/
 │    ├── auth.py
 │    ├── documents.py
 │    └── admin.py
 ├── templates/
 │    ├── base.html
 │    ├── index.html
 │    ├── login.html
 │    ├── register.html
 │    ├── admin_user_details.html
 │    ├── compare_side.html
 │    ├── compare.html
 │    ├── upload.html
 │    ├── profile.html
 │    ├── analytics.html
 │    ├── matches.html
 │    ├── admin_credit_requests.html
 │    └── credit_request.html
 ├── static/
 │    ├── style.css
 │    └── script.js
 ├── utils/
 │    ├── nlp_utils.py
 └── database.db   (created on first run)


## Setup Instructions

1. **Clone the Repository**  
   Clone the project repository to your local machine:
   ```bash
   git clone https://github.com/akupadhyay8/smart-document-scanner
   cd Document_Scanner

## Install Dependencies
### Install the required Python packages:
includes Flask, APScheduler, python-dotenv, sentence-transformers (if using AI matching), and any other required packages.

## Initialize the Database & Run the Application
The database is automatically initialized when you run the app for the first time. Start the application:
```bash
python app.py

