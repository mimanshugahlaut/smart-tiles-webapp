#!/usr/bin/env python3
"""
Smart Tile System - Setup Verification Script
Run this to check if everything is configured correctly
"""

import os
import sys
import sqlite3

def check_file(filepath, description):
    """Check if a file exists"""
    if os.path.exists(filepath):
        size = os.path.getsize(filepath)
        print(f"✅ {description:40s} ({size:,} bytes)")
        return True
    else:
        print(f"❌ {description:40s} MISSING!")
        return False

def check_directory(dirpath, description):
    """Check if a directory exists"""
    if os.path.isdir(dirpath):
        count = len(os.listdir(dirpath))
        print(f"✅ {description:40s} ({count} items)")
        return True
    else:
        print(f"❌ {description:40s} MISSING!")
        return False

def check_database():
    """Check database structure"""
    print("\n" + "="*70)
    print("💾 DATABASE CHECK")
    print("="*70)
    
    if not os.path.exists('smart_tiles.db'):
        print("⚠️  Database not found (will be created on first run)")
        return True
    
    try:
        conn = sqlite3.connect('smart_tiles.db')
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cursor.fetchall()]
        
        expected_tables = ['users', 'password_reset_tokens']
        for table in expected_tables:
            if table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"✅ Table '{table:25s}' exists ({count} rows)")
            else:
                print(f"❌ Table '{table:25s}' MISSING!")
        
        # Check users table structure
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        expected_columns = ['id', 'username', 'email', 'password_hash', 'created_at', 'last_login']
        
        print("\n   Users table columns:")
        for col in expected_columns:
            status = "✅" if col in columns else "❌"
            print(f"   {status} {col}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    print(f"\n🐍 Python Version: {version.major}.{version.minor}.{version.micro}")
    if version.major >= 3 and version.minor >= 7:
        print("✅ Python version is compatible")
        return True
    else:
        print("❌ Python 3.7+ required")
        return False

def check_dependencies():
    """Check installed packages"""
    print("\n" + "="*70)
    print("📦 DEPENDENCIES CHECK")
    print("="*70)
    
    required = {
        'flask': 'Flask',
        'flask_cors': 'Flask-CORS',
        'werkzeug': 'Werkzeug',
        'dotenv': 'python-dotenv'
    }
    
    all_installed = True
    for module, package in required.items():
        try:
            __import__(module)
            print(f"✅ {package:30s} installed")
        except ImportError:
            print(f"❌ {package:30s} NOT INSTALLED")
            all_installed = False
    
    if not all_installed:
        print("\n💡 Install missing packages:")
        print("   pip install -r requirements.txt")
    
    return all_installed

def main():
    """Main verification function"""
    print("\n" + "="*70)
    print("🔍 SMART TILE SYSTEM - SETUP VERIFICATION")
    print("="*70)
    
    all_good = True
    
    # Check Python version
    all_good = check_python_version() and all_good
    
    # Check core files
    print("\n" + "="*70)
    print("📄 CORE FILES")
    print("="*70)
    
    core_files = {
        'app.py': 'Main Flask Application',
        'config.py': 'Configuration File',
        'email_service.py': 'Email Service',
        'requirements.txt': 'Dependencies List',
        '.env.example': 'Environment Template'
    }
    
    for file, desc in core_files.items():
        all_good = check_file(file, desc) and all_good
    
    # Check directories
    print("\n" + "="*70)
    print("📁 DIRECTORIES")
    print("="*70)
    
    directories = {
        'templates': 'HTML Templates',
        'static': 'Static Files',
        'static/css': 'CSS Stylesheets',
        'static/js': 'JavaScript Files'
    }
    
    for dir_path, desc in directories.items():
        all_good = check_directory(dir_path, desc) and all_good
    
    # Check templates
    print("\n" + "="*70)
    print("🎨 HTML TEMPLATES")
    print("="*70)
    
    templates = [
        'login.html',
        'register.html',
        'forgot_password.html',
        'reset_password.html',
        'dashboard.html',
        'profile.html',
        'settings.html'
    ]
    
    for template in templates:
        all_good = check_file(f'templates/{template}', template) and all_good
    
    # Check CSS files
    print("\n" + "="*70)
    print("💅 CSS STYLESHEETS")
    print("="*70)
    
    css_files = ['style.css', 'dashboard.css']
    for css in css_files:
        all_good = check_file(f'static/css/{css}', css) and all_good
    
    # Check JS files
    print("\n" + "="*70)
    print("⚡ JAVASCRIPT FILES")
    print("="*70)
    
    js_files = ['auth.js', 'dashboard.js', 'profile.js', 'settings.js']
    for js in js_files:
        all_good = check_file(f'static/js/{js}', js) and all_good
    
    # Check dependencies
    all_good = check_dependencies() and all_good
    
    # Check database
    all_good = check_database() and all_good
    
    # Check .env file (optional)
    print("\n" + "="*70)
    print("🔐 CONFIGURATION")
    print("="*70)
    
    if os.path.exists('.env'):
        print("✅ .env file found (Email configured)")
    else:
        print("⚠️  .env file not found (Using development mode)")
        print("   Email reset links will appear in console")
        print("   See .env.example and EMAIL_SETUP.md to configure")
    
    # Final summary
    print("\n" + "="*70)
    print("📊 SUMMARY")
    print("="*70)
    
    if all_good:
        print("✅ All checks passed! Your setup is complete.")
        print("\n🚀 Ready to run:")
        print("   python app.py")
        print("\n🌐 Then open:")
        print("   http://localhost:5000")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\n💡 Common fixes:")
        print("   1. Make sure all files are in the correct folders")
        print("   2. Install dependencies: pip install -r requirements.txt")
        print("   3. Check file permissions")
    
    print("="*70 + "\n")
    
    return 0 if all_good else 1

if __name__ == '__main__':
    sys.exit(main())