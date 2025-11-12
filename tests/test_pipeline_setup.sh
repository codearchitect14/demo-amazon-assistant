#!/bin/bash

# Test script to verify Bitbucket pipeline setup
echo "Testing Bitbucket pipeline setup..."

# Check Python version
echo "Python version:"
python --version

# Create virtual environment
echo "Creating virtual environment..."
python -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check Python version in venv
echo "Python version in venv:"
python --version

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Test imports
echo "Testing imports..."
python -c "import streamlit; print('Streamlit imported successfully')"
python -c "import fastapi; print('FastAPI imported successfully')"
python -c "import langchain; print('LangChain imported successfully')"

echo "Pipeline setup test completed successfully!" 