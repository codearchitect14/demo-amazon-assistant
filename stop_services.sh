#!/bin/bash

echo "🛑 Stopping RAG Demo Services..."

# Kill processes on common ports
echo "🔍 Looking for processes on ports 3001, 8501, and 6379..."

# Kill processes on port 3001 (API)
lsof -ti:3001 | xargs kill -9 2>/dev/null || echo "No processes found on port 3001"

# Kill processes on port 8501 (Streamlit)
lsof -ti:8501 | xargs kill -9 2>/dev/null || echo "No processes found on port 8501"

# Kill processes on port 6379 (Redis)
lsof -ti:6379 | xargs kill -9 2>/dev/null || echo "No processes found on port 6379"

# Kill any Python processes that might be running the services
pkill -f "uvicorn.*app.api:app" 2>/dev/null || echo "No uvicorn API processes found"
pkill -f "streamlit.*run.*app.py" 2>/dev/null || echo "No streamlit processes found"

# Stop Redis processes
echo "🔴 Stopping Redis processes..."
pkill -f "redis-server" 2>/dev/null || echo "No redis-server processes found"

# Stop Redis Docker container if running
echo "🐳 Stopping Redis Docker container..."
docker stop rag-redis 2>/dev/null || echo "No Redis Docker container found"
docker rm rag-redis 2>/dev/null || echo "No Redis Docker container to remove"

# Stop Redis via Homebrew if it was started that way
echo "🍺 Stopping Redis via Homebrew..."
brew services stop redis 2>/dev/null || echo "No Redis Homebrew service found"

echo "✅ All services stopped" 