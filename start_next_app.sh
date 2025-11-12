#!/bin/bash

# Start RAG Chatbot Application with Next.js Frontend
echo "🎯 Starting RAG Chatbot Application (Next.js)"
echo "=================================================="

# Check if Python script exists
if [ ! -f "run_next_app.py" ]; then
    echo "❌ Error: run_next_app.py not found"
    exit 1
fi

# Run the Python script
python3 run_next_app.py 