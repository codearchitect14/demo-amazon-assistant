#!/usr/bin/env python3
"""
Startup script for Advanced RAG Application
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def check_environment():
    """Check if required environment variables are set"""
    print("🔍 Checking environment...")

    required_vars = [
        "GROQ_API_KEY",
    ]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file")
        return False

    print("✅ Environment variables are set")
    return True


def check_dependencies():
    """Check if required dependencies are available"""
    print("📦 Checking dependencies...")

    try:
        import fastapi
        import uvicorn
        import groq
        import qdrant_client
        import sentence_transformers
        import langchain

        print("✅ Core dependencies available")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        return False

    return True


def start_api_server():
    """Start the FastAPI server"""
    print("🚀 Starting API server...")

    try:
        import uvicorn
        from app.api import app
        import socket

        # Find available port for API
        api_port = 8000
        while api_port < 8010:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("localhost", api_port))
                    break
            except OSError:
                api_port += 1

        if api_port >= 8010:
            print("❌ No available ports found for API server")
            return None

        # Get configuration
        host = os.getenv("API_HOST", "0.0.0.0")

        print(f"🌐 Server will be available at: http://{host}:{api_port}")
        print(
            f"📚 API Documentation will be available at: http://localhost:{api_port}/docs"
        )

        # Start server
        uvicorn.run(
            "app.api:app", host=host, port=api_port, reload=True, log_level="info"
        )

    except Exception as e:
        print(f"❌ Error starting server: {e}")
        logger.error(f"Server startup error: {e}")


def start_streamlit_app():
    """Start the Streamlit app"""
    print("🎨 Starting Streamlit app...")

    try:
        import subprocess
        import sys
        import socket

        # Find available port for Streamlit
        streamlit_port = 8501
        while streamlit_port < 8510:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(("localhost", streamlit_port))
                    break
            except OSError:
                streamlit_port += 1

        if streamlit_port >= 8510:
            print("❌ No available ports found for Streamlit app")
            return None

        print(f"🎨 Streamlit will be available at: http://localhost:{streamlit_port}")

        # Start Streamlit
        subprocess.run(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "app/app.py",
                "--server.port",
                str(streamlit_port),
                "--server.address",
                "0.0.0.0",
            ]
        )

    except Exception as e:
        print(f"❌ Error starting Streamlit: {e}")
        logger.error(f"Streamlit startup error: {e}")


def main():
    """Main startup function"""
    print("🎯 Advanced RAG Application Startup")
    print("=" * 50)

    # Check environment
    if not check_environment():
        sys.exit(1)

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    print("\n🎉 All checks passed! Starting application...")

    # Ask user what to start
    print("\nWhat would you like to start?")
    print("1. API Server (FastAPI)")
    print("2. Web Interface (Streamlit)")
    print("3. Both")
    print("4. Test the system")

    try:
        choice = input("\nEnter your choice (1-4): ").strip()

        if choice == "1":
            start_api_server()
        elif choice == "2":
            start_streamlit_app()
        elif choice == "3":
            print("Starting both services...")
            import subprocess
            import sys
            import time

            # Start API server in background
            api_process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "app.api:app",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    "8000",
                    "--reload",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            print("🚀 API server starting in background...")
            time.sleep(3)

            # Start Streamlit in foreground
            print("🎨 Starting Streamlit app...")
            streamlit_process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "streamlit",
                    "run",
                    "app/app.py",
                    "--server.port",
                    "8501",
                    "--server.address",
                    "0.0.0.0",
                ]
            )

            try:
                # Wait for Streamlit to finish
                streamlit_process.wait()
            except KeyboardInterrupt:
                print("\n👋 Shutting down...")
                api_process.terminate()
                streamlit_process.terminate()
        elif choice == "4":
            print("Running system test...")
            import subprocess

            subprocess.run([sys.executable, "test_advanced_rag.py"])
        else:
            print("Invalid choice. Starting API server by default...")
            start_api_server()

    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Startup error: {e}")


if __name__ == "__main__":
    main()
