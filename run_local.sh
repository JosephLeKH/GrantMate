#!/bin/bash
# Simple script to run the backend and frontend locally

echo "Starting PHC Grant Copilot..."
echo ""

# Check if Python dependencies are installed
if ! python3 -c "import fastapi, uvicorn" 2>/dev/null; then
    echo "Installing Python dependencies..."
    pip3 install -r requirements.txt
fi

# Check if Node dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies..."
    npm install
fi

# Start the backend server in the background
echo "Starting backend server on http://localhost:8000"
uvicorn main:app --host 127.0.0.1 --port 8000 --reload &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 2

# Start the frontend dev server
echo "Starting frontend dev server on http://localhost:8080"
echo ""
echo "Backend API: http://localhost:8000"
echo "Frontend: http://localhost:8080"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Trap Ctrl+C to kill both processes
trap "echo ''; echo 'Stopping servers...'; kill $BACKEND_PID 2>/dev/null; exit" INT

# Start frontend (this will run in foreground)
npm run dev

