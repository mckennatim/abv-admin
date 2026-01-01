
#!/bin/bash
echo "🚀 Starting complete dual server setup with nohup..."

# Step 1: Kill any existing Python processes
echo "Stopping all existing Python processes..."
taskkill //F //IM python.exe 2>/dev/null || echo "No Python processes found"
sleep 2

# Step 2: Start static file server on port 8000 (background)
echo "Starting static file server on port 8000..."
cd "C:/Users/mcken/OneDrive/chorus/abv/tech"
python -m http.server 8000 > static.log 2>&1 &
STATIC_PID=$!
echo "Static server PID: $STATIC_PID"
sleep 2

# Step 3: Start Flask API server with nohup (should get port 8001)
echo "Starting Flask API server with nohup..."
cd "C:/Users/mcken/OneDrive/chorus/abv/tech/abv/server"
nohup "C:\Users\mcken\miniconda3\python.exe" app.py > nohup.out 2>&1 &
FLASK_PID=$!
echo "Flask server PID: $FLASK_PID"
sleep 3

# Step 4: Verify both servers are running
echo ""
echo "🔍 Checking server status:"
netstat -an | findstr ":8000" && echo "✅ Port 8000: Static files running"
netstat -an | findstr ":8001" && echo "✅ Port 8001: Flask API running"