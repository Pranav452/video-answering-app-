#!/bin/bash

# Lecture Intelligence Application Startup Script

echo "🎓 Starting Lecture Intelligence Application..."
echo "=============================================="

# Check if required commands exist
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 is required but not installed. Aborting." >&2; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js is required but not installed. Aborting." >&2; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "❌ npm is required but not installed. Aborting." >&2; exit 1; }

# Function to check if port is in use
check_port() {
    lsof -i :$1 >/dev/null 2>&1
}

# Check if ports are available
if check_port 8000; then
    echo "⚠️  Port 8000 is already in use. Please stop any existing backend services."
    exit 1
fi

if check_port 3000; then
    echo "⚠️  Port 3000 is already in use. Please stop any existing frontend services."
    exit 1
fi

# Check environment variables
if [ ! -f "backend/.env" ]; then
    echo "⚠️  Backend .env file not found. Please create backend/.env with:"
    echo "   GEMINI_API_KEY=your_gemini_api_key_here"
    echo ""
    echo "📝 Creating example .env file..."
    cat > backend/.env << EOF
# Google Gemini API Key (required)
GEMINI_API_KEY=your_gemini_api_key_here

# Optional: Uncomment to use different Whisper model
# WHISPER_MODEL=base  # Options: tiny, base, small, medium, large, large-v2, large-v3
EOF
    echo "✅ Created backend/.env - Please add your Gemini API key"
fi

if [ ! -f "frontend/.env.local" ]; then
    echo "📝 Creating frontend environment file..."
    cat > frontend/.env.local << EOF
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
    echo "✅ Created frontend/.env.local"
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."

# Backend dependencies - Create virtual environment if it doesn't exist
if [ ! -d "backend/venv" ]; then
    echo "🔧 Creating Python virtual environment..."
    cd backend
    python3 -m venv venv
    cd ..
    echo "✅ Virtual environment created"
fi

# Activate virtual environment and install dependencies
echo "🔧 Installing backend dependencies..."
cd backend
source venv/bin/activate
pip install -r requirements.txt
cd ..
echo "✅ Backend dependencies installed"

# Frontend dependencies
if [ ! -d "frontend/node_modules" ]; then
    echo "🔧 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
    echo "✅ Frontend dependencies installed"
fi

# Start services
echo "🚀 Starting services..."

# Start backend in background
echo "📡 Starting backend server on http://localhost:8000..."
cd backend
source venv/bin/activate
python main.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Check if backend is running
if ! curl -s http://localhost:8000 > /dev/null; then
    echo "❌ Backend failed to start. Check the logs above for errors."
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

echo "✅ Backend server started successfully!"

# Start frontend in background
echo "🌐 Starting frontend server on http://localhost:3000..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
echo "⏳ Waiting for frontend to start..."
sleep 10

echo ""
echo "🎉 Lecture Intelligence Application is ready!"
echo "=============================================="
echo "📡 Backend API: http://localhost:8000"
echo "📊 API Documentation: http://localhost:8000/docs"
echo "🌐 Frontend: http://localhost:3000"
echo ""
echo "📝 Usage:"
echo "1. Open http://localhost:3000 in your browser"
echo "2. Upload a lecture video file"
echo "3. Wait for processing to complete"
echo "4. Start chatting with your lecture content!"
echo ""
echo "⚠️  Important Notes:"
echo "• Make sure you have added your Gemini API key to backend/.env"
echo "• Video processing may take 2-5 minutes depending on video length"
echo "• Supported formats: MP4, AVI, MOV, MKV, WebM (max 2GB)"
echo ""
echo "🛑 To stop the application:"
echo "   Press Ctrl+C or run: kill $BACKEND_PID $FRONTEND_PID"
echo ""

# Wait for user to stop
trap "echo '🛑 Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT
wait 