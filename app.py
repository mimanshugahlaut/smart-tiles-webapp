from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime, timedelta
import secrets

# Try to import config and email service, but don't fail if missing
try:
    from config import Config
    from email_service import EmailService
    email_service = EmailService()
except ImportError:
    print("Warning: config.py or email_service.py not found. Using defaults.")
    class Config:
        SECRET_KEY = 'dev-secret-key-change-in-production'
        DATABASE = 'smart_tiles.db'
        RESET_TOKEN_EXPIRY_HOURS = 1
    email_service = None

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY'] if hasattr(app.config, 'SECRET_KEY') else 'dev-secret-key'
CORS(app)

# Database configuration
DATABASE = app.config.get('DATABASE', 'smart_tiles.db')

def get_db():
    """Create database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with users table"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN DEFAULT 0
        )
    ''')
    
    # NEW: Energy data table for simulation
    cursor.execute('''
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
    ''')
    
    # Create index for faster queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_energy_user_time 
        ON energy_data(user_id, timestamp)
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully")

# Initialize database on startup
try:
    init_db()
except Exception as e:
    print(f"❌ Database initialization error: {e}")

@app.route('/')
def index():
    """Landing page - redirect to login or dashboard"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration endpoint"""
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            print(f"📝 Registration attempt - Username: {username}, Email: {email}")
            
            # Validation
            errors = []
            
            if not username or len(username) < 3:
                errors.append('Username must be at least 3 characters long')
            
            if not email or '@' not in email:
                errors.append('Valid email address is required')
            
            if not password or len(password) < 6:
                errors.append('Password must be at least 6 characters long')
            
            if password != confirm_password:
                errors.append('Passwords do not match')
            
            if errors:
                for error in errors:
                    flash(error, 'error')
                    print(f"❌ Validation error: {error}")
                return render_template('register.html')
            
            # Check if user already exists
            conn = get_db()
            cursor = conn.cursor()
            
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                flash('Username already taken', 'error')
                print(f"❌ Username '{username}' already exists")
                conn.close()
                return render_template('register.html')
            
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            if cursor.fetchone():
                flash('Email already registered', 'error')
                print(f"❌ Email '{email}' already exists")
                conn.close()
                return render_template('register.html')
            
            # Create new user
            password_hash = generate_password_hash(password)
            
            cursor.execute(
                'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                (username, email, password_hash)
            )
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            
            print(f"✅ User created successfully - ID: {user_id}, Username: {username}")
            
            # Auto-login after registration
            session['user_id'] = user_id
            session['username'] = username
            session['email'] = email
            
            # Send welcome email
            if email_service:
                try:
                    email_service.send_welcome_email(email, username)
                except Exception as e:
                    print(f"⚠️  Could not send welcome email: {e}")
            
            flash('Registration successful! Welcome to Smart Tile System.', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            print(f"❌ Registration error: {e}")
            import traceback
            traceback.print_exc()
            flash('Registration failed. Please try again.', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login endpoint"""
    if request.method == 'POST':
        try:
            identifier = request.form.get('username', '').strip().lower()
            password = request.form.get('password', '')
            
            print(f"🔐 Login attempt - Identifier: {identifier}")
            
            if not identifier or not password:
                flash('Username/Email and password are required', 'error')
                return render_template('login.html')
            
            # Check credentials
            conn = get_db()
            cursor = conn.cursor()
            
            cursor.execute(
                'SELECT id, username, email, password_hash FROM users WHERE username = ? OR email = ?',
                (identifier, identifier)
            )
            user = cursor.fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                # Update last login
                cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', 
                             (datetime.now(), user['id']))
                conn.commit()
                conn.close()
                
                # Create session
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['email'] = user['email']
                
                print(f"✅ Login successful - User: {user['username']}")
                flash(f'Welcome back, {user["username"]}!', 'success')
                return redirect(url_for('dashboard'))
            
            conn.close()
            print(f"❌ Invalid credentials for: {identifier}")
            flash('Invalid username/email or password', 'error')
            return render_template('login.html')
            
        except Exception as e:
            print(f"❌ Login error: {e}")
            import traceback
            traceback.print_exc()
            flash('Login failed. Please try again.', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password - generate reset token"""
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            
            print(f"🔑 Password reset request for: {email}")
            
            if not email:
                flash('Email address is required', 'error')
                return render_template('forgot_password.html')
            
            conn = get_db()
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, username FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            
            if user:
                # Generate reset token
                token = secrets.token_urlsafe(32)
                expires_at = datetime.now() + timedelta(hours=1)
                
                cursor.execute(
                    'INSERT INTO password_reset_tokens (email, token, expires_at) VALUES (?, ?, ?)',
                    (email, token, expires_at)
                )
                conn.commit()
                
                # Generate reset link
                reset_link = url_for('reset_password', token=token, _external=True)
                
                print("\n" + "="*70)
                print("📧 PASSWORD RESET LINK (Copy this URL)")
                print("="*70)
                print(f"User: {user['username']}")
                print(f"Email: {email}")
                print(f"Reset Link:")
                print(f"\n{reset_link}\n")
                print("="*70)
                print("⏰ Link expires in 1 hour")
                print("="*70 + "\n")
                
                # Try to send email
                if email_service:
                    try:
                        email_service.send_password_reset_email(email, reset_link, user['username'])
                    except Exception as e:
                        print(f"⚠️  Could not send email: {e}")
                
                message = 'Password reset link has been generated. Check your terminal/console for the link, or check your email if configured.'
            else:
                print(f"⚠️  No user found with email: {email}")
                # Don't reveal if email exists
                message = 'If an account exists with this email, a reset link has been generated.'
            
            conn.close()
            flash(message, 'info')
            return redirect(url_for('login'))
            
        except Exception as e:
            print(f"❌ Password reset error: {e}")
            import traceback
            traceback.print_exc()
            flash('An error occurred. Please try again.', 'error')
            return render_template('forgot_password.html')
    
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with valid token"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Verify token
        cursor.execute(
            'SELECT email, expires_at, used FROM password_reset_tokens WHERE token = ?',
            (token,)
        )
        token_data = cursor.fetchone()
        
        if not token_data:
            conn.close()
            flash('Invalid reset link', 'error')
            return redirect(url_for('login'))
        
        if token_data['used']:
            conn.close()
            flash('This reset link has already been used', 'error')
            return redirect(url_for('login'))
        
        # Check expiration
        expires_at = datetime.fromisoformat(token_data['expires_at'])
        if expires_at < datetime.now():
            conn.close()
            flash('Reset link has expired', 'error')
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            if not password or len(password) < 6:
                flash('Password must be at least 6 characters long', 'error')
                return render_template('reset_password.html', token=token)
            
            if password != confirm_password:
                flash('Passwords do not match', 'error')
                return render_template('reset_password.html', token=token)
            
            # Update password
            password_hash = generate_password_hash(password)
            cursor.execute('UPDATE users SET password_hash = ? WHERE email = ?',
                          (password_hash, token_data['email']))
            
            # Mark token as used
            cursor.execute('UPDATE password_reset_tokens SET used = 1 WHERE token = ?', (token,))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Password reset successful for: {token_data['email']}")
            flash('Password successfully reset! Please log in.', 'success')
            return redirect(url_for('login'))
        
        conn.close()
        return render_template('reset_password.html', token=token)
        
    except Exception as e:
        conn.close()
        print(f"❌ Reset password error: {e}")
        import traceback
        traceback.print_exc()
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    """Main dashboard - requires authentication"""
    if 'user_id' not in session:
        flash('Please log in to access the dashboard', 'warning')
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', username=session.get('username'))

@app.route('/profile')
def profile():
    """User profile page"""
    if 'user_id' not in session:
        flash('Please log in to access your profile', 'warning')
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT username, email, created_at, last_login FROM users WHERE id = ?', 
                   (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    
    return render_template('profile.html', user=user)

@app.route('/settings')
def settings():
    """User settings page"""
    if 'user_id' not in session:
        flash('Please log in to access settings', 'warning')
        return redirect(url_for('login'))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT username, email FROM users WHERE id = ?', (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    
    return render_template('settings.html', user=user)

@app.route('/update-profile', methods=['POST'])
def update_profile():
    """Update user profile"""
    if 'user_id' not in session:
        flash('Please log in', 'error')
        return redirect(url_for('login'))
    
    try:
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        
        if not username or len(username) < 3:
            flash('Username must be at least 3 characters', 'error')
            return redirect(url_for('profile'))
        
        if not email or '@' not in email:
            flash('Valid email is required', 'error')
            return redirect(url_for('profile'))
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Check if username/email taken by another user
        cursor.execute('SELECT id FROM users WHERE (username = ? OR email = ?) AND id != ?', 
                       (username, email, session['user_id']))
        if cursor.fetchone():
            flash('Username or email already taken', 'error')
            conn.close()
            return redirect(url_for('profile'))
        
        cursor.execute('UPDATE users SET username = ?, email = ? WHERE id = ?',
                       (username, email, session['user_id']))
        conn.commit()
        conn.close()
        
        session['username'] = username
        session['email'] = email
        
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
        
    except Exception as e:
        print(f"❌ Update profile error: {e}")
        flash('Failed to update profile', 'error')
        return redirect(url_for('profile'))

@app.route('/change-password', methods=['POST'])
def change_password():
    """Change user password"""
    if 'user_id' not in session:
        flash('Please log in', 'error')
        return redirect(url_for('login'))
    
    try:
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not current_password:
            flash('Current password is required', 'error')
            return redirect(url_for('settings'))
        
        if not new_password or len(new_password) < 6:
            flash('New password must be at least 6 characters', 'error')
            return redirect(url_for('settings'))
        
        if new_password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('settings'))
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        
        if not check_password_hash(user['password_hash'], current_password):
            flash('Current password is incorrect', 'error')
            conn.close()
            return redirect(url_for('settings'))
        
        new_hash = generate_password_hash(new_password)
        cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?',
                       (new_hash, session['user_id']))
        conn.commit()
        conn.close()
        
        flash('Password changed successfully!', 'success')
        return redirect(url_for('settings'))
        
    except Exception as e:
        print(f"❌ Change password error: {e}")
        flash('Failed to change password', 'error')
        return redirect(url_for('settings'))

@app.route('/delete-account', methods=['POST'])
def delete_account():
    """Delete user account"""
    if 'user_id' not in session:
        flash('Please log in', 'error')
        return redirect(url_for('login'))
    
    try:
        password = request.form.get('password', '')
        
        if not password:
            flash('Password is required to delete account', 'error')
            return redirect(url_for('settings'))
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash, email FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        
        if not check_password_hash(user['password_hash'], password):
            flash('Incorrect password', 'error')
            conn.close()
            return redirect(url_for('settings'))
        
        # Delete user and related data
        cursor.execute('DELETE FROM password_reset_tokens WHERE email = ?', (user['email'],))
        cursor.execute('DELETE FROM users WHERE id = ?', (session['user_id'],))
        conn.commit()
        conn.close()
        
        session.clear()
        flash('Your account has been deleted', 'info')
        return redirect(url_for('login'))
        
    except Exception as e:
        print(f"❌ Delete account error: {e}")
        flash('Failed to delete account', 'error')
        return redirect(url_for('settings'))

@app.route('/logout')
def logout():
    """Logout user"""
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye, {username}! You have been logged out.', 'info')
    return redirect(url_for('login'))

# ============================================================================
# EXPERIMENT 9: ENERGY SIMULATION MODULE
# ============================================================================

@app.route('/simulate-step', methods=['POST'])
def simulate_step():
    """Simulate a footstep and generate energy data"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        import random
        
        # Simulate realistic piezoelectric parameters
        # Force: 400-800 N (typical adult footstep)
        # Displacement: 2-5 mm (piezoelectric compression)
        force = random.uniform(400, 800)  # Newtons
        displacement = random.uniform(0.002, 0.005)  # Meters
        
        # Energy formula: E = Force × Displacement
        energy_generated = force * displacement  # Joules
        
        # Convert to more readable units (millijoules)
        energy_mj = energy_generated * 1000
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Get current footstep count for user
        cursor.execute(
            'SELECT COALESCE(MAX(footsteps), 0) FROM energy_data WHERE user_id = ?',
            (session['user_id'],)
        )
        current_steps = cursor.fetchone()[0]
        new_step_count = current_steps + 1
        
        # Insert energy data
        cursor.execute('''
            INSERT INTO energy_data 
            (user_id, footsteps, force, displacement, energy_generated)
            VALUES (?, ?, ?, ?, ?)
        ''', (session['user_id'], new_step_count, force, displacement, energy_generated))
        
        conn.commit()
        
        # Get updated statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_steps,
                SUM(energy_generated) as total_energy,
                AVG(energy_generated) as avg_energy
            FROM energy_data 
            WHERE user_id = ?
        ''', (session['user_id'],))
        
        stats = cursor.fetchone()
        conn.close()
        
        print(f"⚡ Energy generated - User: {session['username']}, Step: {new_step_count}, Energy: {energy_mj:.2f} mJ")
        
        return jsonify({
            'success': True,
            'data': {
                'step_number': new_step_count,
                'force': round(force, 2),
                'displacement': round(displacement * 1000, 3),  # Convert to mm
                'energy': round(energy_mj, 2),  # millijoules
                'total_steps': stats['total_steps'],
                'total_energy': round(stats['total_energy'] * 1000, 2),  # mJ
                'avg_energy': round(stats['avg_energy'] * 1000, 2) if stats['avg_energy'] else 0
            }
        })
        
    except Exception as e:
        print(f"❌ Simulation error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Simulation failed'}), 500

@app.route('/get-energy-data', methods=['GET'])
def get_energy_data():
    """Get energy data for charts and statistics"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        limit = request.args.get('limit', 50, type=int)
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Get recent energy data ordered by timestamp (oldest to newest for chart)
        cursor.execute('''
            SELECT 
                id,
                footsteps,
                timestamp,
                force,
                displacement,
                energy_generated
            FROM energy_data
            WHERE user_id = ?
            ORDER BY timestamp ASC
            LIMIT ?
        ''', (session['user_id'], limit))
        
        all_records = cursor.fetchall()
        
        # Get summary statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_steps,
                SUM(energy_generated) as total_energy,
                AVG(energy_generated) as avg_energy,
                MAX(energy_generated) as max_energy,
                MIN(energy_generated) as min_energy
            FROM energy_data 
            WHERE user_id = ?
        ''', (session['user_id'],))
        
        stats = cursor.fetchone()
        conn.close()
        
        # Format data for charts - use step numbers as labels
        chart_data = {
            'labels': [],
            'energy': []
        }
        
        if all_records:
            # Use step numbers for X-axis labels
            for row in all_records:
                chart_data['labels'].append(f"Step {row['footsteps']}")
                chart_data['energy'].append(round(row['energy_generated'] * 1000, 2))
        
        # Format recent records (last 10 for table, newest first)
        recent_records = [{
            'id': row['id'],
            'step': row['footsteps'],
            'time': row['timestamp'],
            'force': round(row['force'], 2),
            'displacement': round(row['displacement'] * 1000, 3),
            'energy': round(row['energy_generated'] * 1000, 2)
        } for row in reversed(all_records[-10:])]
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_steps': stats['total_steps'] or 0,
                'total_energy': round((stats['total_energy'] or 0) * 1000, 2),
                'avg_energy': round((stats['avg_energy'] or 0) * 1000, 2),
                'max_energy': round((stats['max_energy'] or 0) * 1000, 2),
                'min_energy': round((stats['min_energy'] or 0) * 1000, 2),
                'total_energy_wh': round((stats['total_energy'] or 0) / 3.6, 4)
            },
            'chart_data': chart_data,
            'recent_records': recent_records
        })
        
    except Exception as e:
        print(f"❌ Get energy data error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Failed to retrieve data'}), 500

@app.route('/clear-data', methods=['POST'])
def clear_data():
    """Clear all energy simulation data for the logged-in user"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get count before deletion
        cursor.execute(
            'SELECT COUNT(*) FROM energy_data WHERE user_id = ?',
            (session['user_id'],)
        )
        count_before = cursor.fetchone()[0]
        
        # Delete all energy data for this user
        cursor.execute(
            'DELETE FROM energy_data WHERE user_id = ?',
            (session['user_id'],)
        )
        
        conn.commit()
        conn.close()
        
        print(f"🗑️  Data cleared - User: {session['username']}, Records deleted: {count_before}")
        
        return jsonify({
            'success': True,
            'message': f'Cleared {count_before} records',
            'records_deleted': count_before
        })
        
    except Exception as e:
        print(f"❌ Clear data error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'Failed to clear data'}), 500

@app.route('/get-dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    """Get real-time dashboard statistics"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # Get comprehensive statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_steps,
                SUM(energy_generated) as total_energy,
                AVG(energy_generated) as avg_energy
            FROM energy_data 
            WHERE user_id = ?
        ''', (session['user_id'],))
        
        stats = cursor.fetchone()
        
        # Get today's statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as steps_today,
                SUM(energy_generated) as energy_today
            FROM energy_data 
            WHERE user_id = ? 
            AND date(timestamp) = date('now')
        ''', (session['user_id'],))
        
        today_stats = cursor.fetchone()
        
        conn.close()
        
        total_energy_j = stats['total_energy'] or 0
        energy_today_j = today_stats['energy_today'] or 0
        
        return jsonify({
            'success': True,
            'total_steps': stats['total_steps'] or 0,
            'total_energy_mj': round(total_energy_j * 1000, 2),
            'total_energy_wh': round(total_energy_j / 3.6, 4),
            'avg_energy': round((stats['avg_energy'] or 0) * 1000, 2),
            'steps_today': today_stats['steps_today'] or 0,
            'energy_today': round(energy_today_j * 1000, 2),
            'energy_value_inr': round(total_energy_j / 3600 * 8, 2)  # Rs 8 per kWh
        })
        
    except Exception as e:
        print(f"❌ Dashboard stats error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get statistics'}), 500

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 SMART TILE SYSTEM STARTING")
    print("="*70)
    print(f"📁 Database: {DATABASE}")
    print(f"🌐 URL: http://localhost:5000")
    print("="*70 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)