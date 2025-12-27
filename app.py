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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        username = request.form['username']
        email = request.form['email'].lower()
        password = request.form['password']
        confirm = request.form['confirm_password']

        if password != confirm:
            flash("Passwords do not match", "error")
            return render_template('register.html')

        conn = get_db()
        cursor = conn.cursor()
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
        identifier = request.form['username']
        password = request.form['password']

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
            return redirect(url_for('dashboard'))

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
# ENERGY SIMULATION
# =====================================================
@app.route('/simulate-step', methods=['POST'])
def simulate_step():
    if 'user_id' not in session:
        return jsonify({'success': False}), 401

    force = random.uniform(400, 800)
    displacement = random.uniform(0.002, 0.005)
    energy = force * displacement

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COALESCE(MAX(footsteps), 0) FROM energy_data WHERE user_id=?",
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
# DASHBOARD DATA (BUG-2 FIX)
# =====================================================
@app.route('/get-energy-data')
def get_energy_data():
    if 'user_id' not in session:
        return jsonify({'success': False}), 401

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT footsteps, timestamp, force, displacement, energy_generated
        FROM energy_data
        WHERE user_id=?
        ORDER BY id DESC
        LIMIT 10
    """, (session['user_id'],))
    rows = cursor.fetchall()

    cursor.execute("""
        SELECT
            COUNT(*),
            COALESCE(SUM(energy_generated),0),
            COALESCE(AVG(energy_generated),0)
        FROM energy_data
        WHERE user_id=?
    """, (session['user_id'],))
    total_steps, total_energy, avg_energy = cursor.fetchone()
    conn.close()

    records = [{
        "step": r["footsteps"],
        "time": r["timestamp"],
        "force": round(r["force"], 2),
        "displacement": round(r["displacement"] * 1000, 3),
        "energy": round(r["energy_generated"] * 1000, 2)
    } for r in rows]

    return jsonify({
        "success": True,
        "statistics": {
            "total_steps": total_steps,
            "total_energy_mj": round(total_energy * 1000, 2),
            "total_energy_wh": round(total_energy / 3.6, 4),
            "avg_energy": round(avg_energy * 1000, 2),
            "energy_value_inr": round((total_energy / 3600) * 8, 2)
        },
        "recent_records": records
    })

# =====================================================
# CLEAR DATA
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
