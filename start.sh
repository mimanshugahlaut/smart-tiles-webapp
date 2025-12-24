#!/bin/bash

echo "========================================================================"
echo "🚀 SMART TILE SYSTEM - EASY START"
echo "========================================================================"
echo ""

# Check if database exists
if [ ! -f "smart_tiles.db" ]; then
    echo "⚠️  Database not found. Creating fresh database..."
    python3 reset_database.py << EOF
2
yes
EOF
    echo ""
fi

# Check if app.py exists
if [ ! -f "app.py" ]; then
    echo "❌ ERROR: app.py not found!"
    echo "Make sure you're in the correct directory."
    exit 1
fi

echo "✅ All checks passed!"
echo ""
echo "📋 Quick Tips:"
echo "   - Registration: http://localhost:5000/register"
echo "   - Login: http://localhost:5000/login"
echo "   - Password reset links show in THIS terminal"
echo ""
echo "🔍 Watch this terminal for:"
echo "   ✅ User created successfully"
echo "   ✅ Login successful"
echo "   📧 PASSWORD RESET LINK"
echo ""
echo "========================================================================"
echo "Starting Flask server..."
echo "========================================================================"
echo ""

# Start Flask
python3 app.py