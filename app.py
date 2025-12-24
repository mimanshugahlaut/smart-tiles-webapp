from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime, timedelta
import secrets

# =====================================================
# Environment Configuration (RENDER SAFE)
# =====================================================
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
DATABASE_PATH = os.getenv("DATABASE_PATH", "smart_tiles.db")

# Email service is OPTIONAL
try:
    from email_service import EmailService
    email_service = EmailService()
except Exception:
    email_service = None
    print("⚠️ Email service disabled (safe for deployment)")

# =====================================================
# Flask App Setup
# =====================================================
app = Flask(__name__)
app.secret_key = SECRET_KEY
CORS(app)

DATABASE = DATABASE_PATH

# =====================================================
# Database Utilities
# =====================================================
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS energy_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            footsteps INTEGER NOT NULL,
            force REAL NOT NULL,
            displacement REAL NOT NULL,
            energy_generated REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized")

# Initialize DB safely
try:
    init_db()
except Exception as e:
    print("❌ DB init failed:", e)

# =====================================================
# Routes
# =====================================================
@app.route('/')
def index():
    return redirect(url_for('dashboard')) if 'user_id' in session else redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if not username or not email or password != confirm:
            flash("Invalid input", "error")
            return render_template('register.html')

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE username=? OR email=?", (username, email))
        if cursor.fetchone():
            flash("User already exists", "error")
            conn.close()
            return render_template('register.html')

        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, generate_password_hash(password))
        )
        conn.commit()
        conn.close()

        flash("Registration successful", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form.get('username', '').lower()
        password = request.form.get('password', '')

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username=? OR email=?",
            (identifier, identifier)
        )
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash("Login successful", "success")
            return redirect(url_for('dashboard'))

        flash("Invalid credentials", "error")

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session.get('username'))

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for('login'))

# =====================================================
# ENERGY SIMULATION (NO HARDWARE NEEDED)
# =====================================================
@app.route('/simulate-step', methods=['POST'])
def simulate_step():
    if 'user_id' not in session:
        return jsonify({'success': False}), 401

    import random
    force = random.uniform(400, 800)
    displacement = random.uniform(0.002, 0.005)
    energy = force * displacement

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COALESCE(MAX(footsteps),0) FROM energy_data WHERE user_id=?",
        (session['user_id'],)
    )
    step = cursor.fetchone()[0] + 1

    cursor.execute("""
        INSERT INTO energy_data (user_id, footsteps, force, displacement, energy_generated)
        VALUES (?, ?, ?, ?, ?)
    """, (session['user_id'], step, force, displacement, energy))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "step": step,
        "energy_mj": round(energy * 1000, 2)
    })

# =====================================================
# Production Entry Point
# =====================================================
if __name__ == "__main__":
    print("🚀 Smart Tiles App Running")
    app.run(debug=True, host="0.0.0.0", port=5000)
