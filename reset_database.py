#!/usr/bin/env python3
"""
Database Reset Script
Run this to fix database issues and start fresh
"""

import os
import sqlite3
import sys
from datetime import datetime

DATABASE = 'smart_tiles.db'

def backup_database():
    """Backup existing database"""
    if os.exists(DATABASE):
        backup_name = f"{DATABASE}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            os.rename(DATABASE, backup_name)
            print(f"✅ Existing database backed up to: {backup_name}")
            return True
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False
    return True

def create_fresh_database():
    """Create a fresh database with correct schema"""
    try:
        # Remove old database if exists
        if os.path.exists(DATABASE):
            response = input(f"\n⚠️  Database '{DATABASE}' exists. Delete it? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Operation cancelled")
                return False
            
            # Backup first
            backup_name = f"{DATABASE}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename(DATABASE, backup_name)
            print(f"✅ Old database backed up to: {backup_name}")
        
        # Create new database
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Create users table
        print("📝 Creating users table...")
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')
        
        # Create password_reset_tokens table
        print("📝 Creating password_reset_tokens table...")
        cursor.execute('''
            CREATE TABLE password_reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                used BOOLEAN DEFAULT 0
            )
        ''')
        
        conn.commit()
        
        # Verify tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print("\n✅ Database created successfully!")
        print(f"📊 Tables created: {', '.join(tables)}")
        
        # Show table structure
        print("\n📋 Users table structure:")
        cursor.execute("PRAGMA table_info(users)")
        for row in cursor.fetchall():
            print(f"   - {row[1]} ({row[2]})")
        
        print("\n📋 Password reset tokens table structure:")
        cursor.execute("PRAGMA table_info(password_reset_tokens)")
        for row in cursor.fetchall():
            print(f"   - {row[1]} ({row[2]})")
        
        conn.close()
        
        print("\n" + "="*70)
        print("✅ DATABASE RESET COMPLETE!")
        print("="*70)
        print(f"📁 Database file: {DATABASE}")
        print("🚀 You can now run: python app.py")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error creating database: {e}")
        import traceback
        traceback.print_exc()
        return False

def view_database_contents():
    """View current database contents"""
    if not os.path.exists(DATABASE):
        print(f"❌ Database '{DATABASE}' not found")
        return
    
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        print("\n" + "="*70)
        print("📊 CURRENT DATABASE CONTENTS")
        print("="*70)
        
        # Show users
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"\n👥 Users: {user_count} total")
        
        if user_count > 0:
            cursor.execute("SELECT id, username, email, created_at FROM users")
            print("\n   ID | Username          | Email                      | Created")
            print("   " + "-"*66)
            for row in cursor.fetchall():
                print(f"   {row[0]:<3} | {row[1]:<17} | {row[2]:<26} | {row[3]}")
        
        # Show reset tokens
        cursor.execute("SELECT COUNT(*) FROM password_reset_tokens WHERE used = 0")
        token_count = cursor.fetchone()[0]
        print(f"\n🔑 Active Reset Tokens: {token_count}")
        
        conn.close()
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"❌ Error viewing database: {e}")

def main():
    """Main function"""
    print("\n" + "="*70)
    print("🔧 SMART TILE DATABASE RESET TOOL")
    print("="*70)
    print("\nOptions:")
    print("1. View current database contents")
    print("2. Reset database (create fresh)")
    print("3. Exit")
    print()
    
    choice = input("Enter your choice (1-3): ")
    
    if choice == '1':
        view_database_contents()
    elif choice == '2':
        if create_fresh_database():
            view_database_contents()
    elif choice == '3':
        print("👋 Goodbye!")
        return 0
    else:
        print("❌ Invalid choice")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())