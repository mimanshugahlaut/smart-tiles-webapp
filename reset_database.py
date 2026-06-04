#!/usr/bin/env python3
"""
Smart Tiles — Database Reset Tool
Run this to fix database issues and start fresh.
"""

import os
import sqlite3
import sys
from datetime import datetime

DATABASE = os.getenv("DATABASE_PATH", "smart_tiles.db")


def get_db_info():
    """View current database contents."""
    if not os.path.exists(DATABASE):
        print(f"❌ Database '{DATABASE}' not found.")
        return

    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

        print("\n" + "=" * 60)
        print("📊 CURRENT DATABASE CONTENTS")
        print("=" * 60)

        # Users
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"\n👥 Users: {user_count} total")

        if user_count > 0:
            cursor.execute("SELECT id, username, email, created_at FROM users")
            print("\n   ID | Username         | Email                      | Created")
            print("   " + "-" * 64)
            for row in cursor.fetchall():
                print(f"   {row[0]:<3} | {row[1]:<16} | {row[2]:<26} | {row[3]}")

        # Energy data
        cursor.execute("SELECT COUNT(*) FROM energy_data")
        energy_count = cursor.fetchone()[0]
        print(f"\n⚡ Energy Records: {energy_count} total")

        # Reset tokens
        try:
            cursor.execute("SELECT COUNT(*) FROM password_reset_tokens WHERE used = 0")
            token_count = cursor.fetchone()[0]
            print(f"\n🔑 Active Reset Tokens: {token_count}")
        except Exception:
            pass

        conn.close()
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"❌ Error viewing database: {e}")


def create_fresh_database():
    """Create a fresh database with correct schema."""
    try:
        if os.path.exists(DATABASE):
            response = input(f"\n⚠️  Database '{DATABASE}' exists. Delete it? (yes/no): ")
            if response.lower() != 'yes':
                print("❌ Operation cancelled.")
                return False

            backup_name = f"{DATABASE}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename(DATABASE, backup_name)
            print(f"✅ Old database backed up to: {backup_name}")

        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()

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

        print("📝 Creating energy_data table...")
        cursor.execute('''
            CREATE TABLE energy_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                footsteps INTEGER NOT NULL,
                force REAL NOT NULL,
                displacement REAL NOT NULL,
                energy_generated REAL NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

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

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()

        print("\n" + "=" * 60)
        print("✅ DATABASE RESET COMPLETE!")
        print("=" * 60)
        print(f"📁 Database: {DATABASE}")
        print(f"📊 Tables:   {', '.join(tables)}")
        print("🚀 Run:      python app.py")
        print("=" * 60 + "\n")
        return True

    except Exception as e:
        print(f"\n❌ Error creating database: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "=" * 60)
    print("🔧 SMART TILES DATABASE RESET TOOL")
    print("=" * 60)
    print("\nOptions:")
    print("  1. View current database contents")
    print("  2. Reset database (create fresh)")
    print("  3. Exit")
    print()

    choice = input("Enter your choice (1-3): ").strip()

    if choice == '1':
        get_db_info()
    elif choice == '2':
        if create_fresh_database():
            get_db_info()
    elif choice == '3':
        print("👋 Goodbye!")
        return 0
    else:
        print("❌ Invalid choice")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())