from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import random
import secrets
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# =====================================================
# Environment Configuration
# =====================================================
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
DATABASE_PATH = os.getenv("DATABASE_PATH", "smart_tiles.db")

# =====================================================
# Flask App Setup
# =====================================================
app = Flask(__name__)
app.secret_key = SECRET_KEY
app.permanent_session_lifetime = timedelta(days=7)
CORS(app)

# =====================================================
# Database Utilities
# =====================================================
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
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
        CREATE TABLE IF NOT EXISTS energy_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            footsteps INTEGER NOT NULL,
            force REAL NOT NULL,
            displacement REAL NOT NULL,
            energy_generated REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
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

    conn.commit()
    conn.close()
    print("[OK] Database initialized")

init_db()

# =====================================================
# Auth Helper
# =====================================================
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

# =====================================================
# Root
# =====================================================
@app.route('/')
def index():
    return redirect(url_for('dashboard')) if 'user_id' in session else redirect(url_for('login'))

# =====================================================
# Register
# =====================================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if not username or not email or not password:
            flash("All fields are required.", "error")
            return render_template('register.html')

        if len(username) < 3:
            flash("Username must be at least 3 characters.", "error")
            return render_template('register.html')

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template('register.html')

        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template('register.html')

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username=? OR email=?", (username, email))
        if cursor.fetchone():
            conn.close()
            flash("Username or email already exists.", "error")
            return render_template('register.html')

        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, generate_password_hash(password))
        )
        conn.commit()
        conn.close()

        flash("Account created successfully! Welcome aboard.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

# =====================================================
# Login
# =====================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        identifier = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '')

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? OR email=?", (identifier, identifier))
        user = cursor.fetchone()

        if user and check_password_hash(user['password_hash'], password):
            cursor.execute("UPDATE users SET last_login=CURRENT_TIMESTAMP WHERE id=?", (user['id'],))
            conn.commit()
            conn.close()

            session.permanent = True
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            return redirect(url_for('dashboard'))

        conn.close()
        flash("Invalid username/email or password.", "error")

    return render_template('login.html')

# =====================================================
# Logout
# =====================================================
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))

# =====================================================
# Forgot Password
# =====================================================
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username FROM users WHERE email=?", (email,))
        user = cursor.fetchone()

        if user:
            token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=1)
            cursor.execute(
                "INSERT INTO password_reset_tokens (email, token, expires_at) VALUES (?, ?, ?)",
                (email, token, expires_at.isoformat())
            )
            conn.commit()

            reset_link = url_for('reset_password', token=token, _external=True)
            print(f"\n{'='*60}")
            print(f"[DEV] PASSWORD RESET LINK:")
            print(f"   {reset_link}")
            print(f"{'='*60}\n")

        conn.close()
        flash("If that email is registered, a reset link has been sent (check terminal in dev mode).", "success")
        return redirect(url_for('forgot_password'))

    return render_template('forgot_password.html')

# =====================================================
# Reset Password
# =====================================================
@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM password_reset_tokens WHERE token=? AND used=0",
        (token,)
    )
    token_row = cursor.fetchone()

    if not token_row:
        conn.close()
        flash("Invalid or expired reset link.", "error")
        return redirect(url_for('forgot_password'))

    expires_at = datetime.fromisoformat(token_row['expires_at'])
    if datetime.now() > expires_at:
        conn.close()
        flash("Reset link has expired. Please request a new one.", "error")
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')

        if len(password) < 6:
            conn.close()
            flash("Password must be at least 6 characters.", "error")
            return render_template('reset_password.html', token=token)

        if password != confirm:
            conn.close()
            flash("Passwords do not match.", "error")
            return render_template('reset_password.html', token=token)

        cursor.execute(
            "UPDATE users SET password_hash=? WHERE email=?",
            (generate_password_hash(password), token_row['email'])
        )
        cursor.execute("UPDATE password_reset_tokens SET used=1 WHERE token=?", (token,))
        conn.commit()
        conn.close()

        flash("Password reset successfully! Please log in.", "success")
        return redirect(url_for('login'))

    conn.close()
    return render_template('reset_password.html', token=token)

# =====================================================
# Dashboard
# =====================================================
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=session.get('username'))

# =====================================================
# Profile
# =====================================================
@app.route('/profile')
@login_required
def profile():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT username, email, created_at, last_login FROM users WHERE id=?",
        (session['user_id'],)
    )
    user = cursor.fetchone()

    cursor.execute("""
        SELECT COUNT(*) AS total_steps, COALESCE(SUM(energy_generated), 0) AS total_energy
        FROM energy_data WHERE user_id=?
    """, (session['user_id'],))
    stats = cursor.fetchone()
    conn.close()

    created_at = user['created_at'].split(" ")[0] if user['created_at'] else "N/A"
    last_login = user['last_login'] or "Never"

    return render_template(
        'profile.html',
        username=user['username'],
        email=user['email'],
        created_at=created_at,
        last_login=last_login,
        total_steps=stats['total_steps'],
        total_energy=round(stats['total_energy'] * 1000, 2)
    )

# =====================================================
# Update Profile
# =====================================================
@app.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip().lower()

    if not username or not email:
        flash("Fields cannot be empty.", "error")
        return redirect(url_for('profile'))

    if len(username) < 3:
        flash("Username must be at least 3 characters.", "error")
        return redirect(url_for('profile'))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE (username=? OR email=?) AND id!=?",
        (username, email, session['user_id'])
    )
    if cursor.fetchone():
        conn.close()
        flash("Username or email already in use.", "error")
        return redirect(url_for('profile'))

    cursor.execute(
        "UPDATE users SET username=?, email=? WHERE id=?",
        (username, email, session['user_id'])
    )
    conn.commit()
    conn.close()

    session['username'] = username
    session['email'] = email
    flash("Profile updated successfully!", "success")
    return redirect(url_for('profile'))

# =====================================================
# Settings
# =====================================================
@app.route('/settings')
@login_required
def settings():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) AS cnt FROM energy_data WHERE user_id=?", (session['user_id'],))
    step_count = cursor.fetchone()['cnt']
    conn.close()
    return render_template('settings.html', username=session.get('username'), step_count=step_count)

# =====================================================
# Change Password
# =====================================================
@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_pw = request.form.get('current_password', '')
    new_pw = request.form.get('new_password', '')
    confirm_pw = request.form.get('confirm_password', '')

    if not current_pw or not new_pw or not confirm_pw:
        flash("All fields are required.", "error")
        return redirect(url_for('settings'))

    if len(new_pw) < 6:
        flash("New password must be at least 6 characters.", "error")
        return redirect(url_for('settings'))

    if new_pw != confirm_pw:
        flash("New passwords do not match.", "error")
        return redirect(url_for('settings'))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE id=?", (session['user_id'],))
    user = cursor.fetchone()

    if not check_password_hash(user['password_hash'], current_pw):
        conn.close()
        flash("Current password is incorrect.", "error")
        return redirect(url_for('settings'))

    cursor.execute(
        "UPDATE users SET password_hash=? WHERE id=?",
        (generate_password_hash(new_pw), session['user_id'])
    )
    conn.commit()
    conn.close()

    flash("Password changed successfully!", "success")
    return redirect(url_for('settings'))

# =====================================================
# Simulate Step (Energy)
# =====================================================
@app.route('/simulate-step', methods=['POST'])
@login_required
def simulate_step():
    force = random.uniform(400, 800)        # Newtons
    displacement = random.uniform(0.002, 0.005)  # Meters
    energy_j = force * displacement          # Joules

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COALESCE(MAX(footsteps), 0) FROM energy_data WHERE user_id=?", (session['user_id'],))
    step = cursor.fetchone()[0] + 1

    cursor.execute("""
        INSERT INTO energy_data (user_id, footsteps, force, displacement, energy_generated)
        VALUES (?, ?, ?, ?, ?)
    """, (session['user_id'], step, force, displacement, energy_j))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "step": step,
        "force": round(force, 2),
        "displacement": round(displacement * 1000, 3),
        "energy_mj": round(energy_j * 1000, 2)
    })

# =====================================================
# Get Energy Data (Stats + Table)
# =====================================================
@app.route('/get-energy-data')
@login_required
def get_energy_data():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) AS total_steps, COALESCE(SUM(energy_generated), 0) AS total_energy
        FROM energy_data WHERE user_id=?
    """, (session['user_id'],))
    agg = cursor.fetchone()
    total_steps = agg['total_steps']
    total_energy = agg['total_energy']

    cursor.execute("""
        SELECT footsteps, force, displacement, energy_generated, timestamp
        FROM energy_data WHERE user_id=?
        ORDER BY footsteps DESC LIMIT 10
    """, (session['user_id'],))
    rows = cursor.fetchall()
    conn.close()

    total_energy_mj = round(total_energy * 1000, 2)
    total_energy_wh = round((total_energy * 1000) / 3_600_000, 8)
    avg_energy = round(total_energy_mj / total_steps, 2) if total_steps else 0
    energy_value = round(total_energy_wh * 8, 6)

    return jsonify({
        "success": True,
        "statistics": {
            "total_steps": total_steps,
            "total_energy_mj": total_energy_mj,
            "total_energy_wh": total_energy_wh,
            "avg_energy": avg_energy,
            "energy_value_inr": energy_value
        },
        "recent_records": [
            {
                "step": r["footsteps"],
                "force": round(r["force"], 2),
                "displacement": round(r["displacement"] * 1000, 3),
                "energy": round(r["energy_generated"] * 1000, 2),
                "timestamp": r["timestamp"]
            } for r in rows
        ]
    })

# =====================================================
# Get Chart Data (Time Series)
# =====================================================
@app.route('/get-chart-data')
@login_required
def get_chart_data():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT footsteps, energy_generated, force, displacement, timestamp
        FROM energy_data WHERE user_id=?
        ORDER BY footsteps ASC LIMIT 50
    """, (session['user_id'],))
    rows = cursor.fetchall()
    conn.close()

    return jsonify({
        "success": True,
        "labels": [f"Step {r['footsteps']}" for r in rows],
        "energy": [round(r['energy_generated'] * 1000, 2) for r in rows],
        "force": [round(r['force'], 2) for r in rows]
    })

# =====================================================
# Clear Data
# =====================================================
@app.route('/clear-data', methods=['POST'])
@login_required
def clear_data():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM energy_data WHERE user_id=?", (session['user_id'],))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "All energy data cleared."})

# =====================================================
# Run
# =====================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
