from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import random

# =====================================================
# Environment Configuration
# =====================================================
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
DATABASE_PATH = os.getenv("DATABASE_PATH", "smart_tiles.db")

# =====================================================
# Flask App Setup
# =====================================================
app = Flask(__name__)
app.secret_key = SECRET_KEY
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
            energy_generated REAL NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Database initialized")

init_db()

# =====================================================
# Auth Routes
# =====================================================
@app.route('/')
def index():
    return redirect(url_for('dashboard')) if 'user_id' in session else redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        email = request.form.get('email').strip().lower()
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')

        if not username or not email or password != confirm:
            flash("Invalid input", "error")
            return render_template('register.html')

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM users WHERE username=? OR email=?",
            (username, email)
        )
        if cursor.fetchone():
            conn.close()
            flash("Username or email already exists", "error")
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
        identifier = request.form.get('username').strip().lower()
        password = request.form.get('password')

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username=? OR email=?",
            (identifier, identifier)
        )
        user = cursor.fetchone()

        if user and check_password_hash(user['password_hash'], password):
            cursor.execute(
                "UPDATE users SET last_login=CURRENT_TIMESTAMP WHERE id=?",
                (user['id'],)
            )
            conn.commit()
            conn.close()

            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))

        conn.close()
        flash("Invalid credentials", "error")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# =====================================================
# Dashboard
# =====================================================
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# =====================================================
# Profile Page
# =====================================================
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cursor = conn.cursor()

    # User info
    cursor.execute("""
        SELECT username, email, created_at, last_login
        FROM users WHERE id=?
    """, (session['user_id'],))
    user = cursor.fetchone()

    # Energy stats
    cursor.execute("""
        SELECT COUNT(*) AS steps, COALESCE(SUM(energy_generated),0) AS energy
        FROM energy_data WHERE user_id=?
    """, (session['user_id'],))
    stats = cursor.fetchone()
    conn.close()

    return render_template(
        'profile.html',
        username=user['username'],
        email=user['email'],
        created_at=user['created_at'].split(" ")[0],
        last_login=user['last_login'] or "Never",
        total_steps=stats['steps'],
        total_energy=round(stats['energy'] * 1000, 2)
    )

# =====================================================
# Update Profile (FIXED)
# =====================================================
@app.route('/update-profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    username = request.form.get('username').strip()
    email = request.form.get('email').strip().lower()

    if not username or not email:
        flash("Fields cannot be empty", "error")
        return redirect(url_for('profile'))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM users
        WHERE (username=? OR email=?) AND id!=?
    """, (username, email, session['user_id']))

    if cursor.fetchone():
        conn.close()
        flash("Username or email already in use", "error")
        return redirect(url_for('profile'))

    cursor.execute("""
        UPDATE users SET username=?, email=? WHERE id=?
    """, (username, email, session['user_id']))

    conn.commit()
    conn.close()

    session['username'] = username
    flash("Profile updated successfully", "success")
    return redirect(url_for('profile'))

# =====================================================
# Energy Simulation
# =====================================================
@app.route('/simulate-step', methods=['POST'])
def simulate_step():
    if 'user_id' not in session:
        return jsonify({'success': False}), 401

    force = random.uniform(400, 800)
    displacement = random.uniform(0.002, 0.005)
    energy_j = force * displacement

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
    """, (session['user_id'], step, force, displacement, energy_j))

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "step": step,
        "energy_mj": round(energy_j * 1000, 2)
    })

# =====================================================
# Dashboard Data
# =====================================================
@app.route('/get-energy-data')
def get_energy_data():
    if 'user_id' not in session:
        return jsonify({'success': False}), 401

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT footsteps, force, displacement, energy_generated
        FROM energy_data
        WHERE user_id=?
        ORDER BY footsteps DESC
        LIMIT 10
    """, (session['user_id'],))
    rows = cursor.fetchall()

    cursor.execute("""
        SELECT COUNT(*), COALESCE(SUM(energy_generated),0)
        FROM energy_data WHERE user_id=?
    """, (session['user_id'],))
    total_steps, total_energy = cursor.fetchone()
    conn.close()

    return jsonify({
        "success": True,
        "statistics": {
            "total_steps": total_steps,
            "total_energy_mj": round(total_energy * 1000, 2),
            "total_energy_wh": round((total_energy * 1000) / 3_600_000, 6),
            "avg_energy": round((total_energy * 1000) / total_steps, 2) if total_steps else 0,
            "energy_value_inr": round(((total_energy * 1000) / 3_600_000) * 8, 2)
        },
        "recent_records": [
            {
                "step": r["footsteps"],
                "force": round(r["force"], 2),
                "displacement": round(r["displacement"] * 1000, 3),
                "energy": round(r["energy_generated"] * 1000, 2)
            } for r in rows
        ]
    })

# =====================================================
# Clear Data
# =====================================================
@app.route('/clear-data', methods=['POST'])
def clear_data():
    if 'user_id' not in session:
        return jsonify({'success': False}), 401

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM energy_data WHERE user_id=?", (session['user_id'],))
    conn.commit()
    conn.close()

    return jsonify({"success": True})

# =====================================================
# Run
# =====================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
