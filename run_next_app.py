#!/usr/bin/env python3
"""
Script to run both the API server and Next.js frontend
"""
import subprocess
import time
import sys
import os
import signal
import psutil
import socket
from pathlib import Path


def is_redis_running(host='localhost', port=6379):
    """Check if Redis is running on the specified host and port"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False


def start_redis():
    """Start Redis server if not already running"""
    if is_redis_running():
        print("✅ Redis is already running on localhost:6379")
        return None
    
    print("🔴 Starting Redis server...")
    
    # Try to start Redis using different methods
    redis_process = None
    
    # Method 1: Try using redis-server command
    try:
        redis_process = subprocess.Popen(
            ["redis-server", "--port", "6379"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).parent,
        )
        print("✅ Redis server started using redis-server command")
        return redis_process
    except FileNotFoundError:
        print("⚠️ redis-server command not found, trying alternative methods...")
    
    # Method 2: Try using Docker if available
    try:
        redis_process = subprocess.Popen(
            ["docker", "run", "--rm", "-d", "-p", "6379:6379", "--name", "rag-redis", "redis:alpine"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).parent,
        )
        print("✅ Redis server started using Docker")
        return redis_process
    except FileNotFoundError:
        print("⚠️ Docker not found, trying Homebrew...")
    
    # Method 3: Try using Homebrew on macOS
    try:
        redis_process = subprocess.Popen(
            ["brew", "services", "start", "redis"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).parent,
        )
        print("✅ Redis server started using Homebrew")
        return redis_process
    except FileNotFoundError:
        print("❌ Could not start Redis automatically")
        print("Please start Redis manually using one of these methods:")
        print("1. Install and run: redis-server")
        print("2. Using Docker: docker run -d -p 6379:6379 redis:alpine")
        print("3. Using Homebrew: brew services start redis")
        return None
    
    return redis_process


def stop_redis(redis_process):
    """Stop Redis server"""
    if redis_process:
        print("🛑 Stopping Redis server...")
        try:
            redis_process.terminate()
            redis_process.wait(timeout=5)
            print("✅ Redis server stopped")
        except subprocess.TimeoutExpired:
            redis_process.kill()
            print("✅ Redis server force killed")
        except Exception as e:
            print(f"⚠️ Warning: Could not stop Redis process: {e}")


def kill_process_tree(pid):
    """Kill a process and all its children"""
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        
        # Kill children first
        for child in children:
            try:
                child.terminate()
            except psutil.NoSuchProcess:
                pass
        
        # Kill parent
        try:
            parent.terminate()
        except psutil.NoSuchProcess:
            pass
        
        # Wait a bit then force kill if needed
        time.sleep(2)
        
        # Force kill if still running
        for child in children:
            try:
                if child.is_running():
                    child.kill()
            except psutil.NoSuchProcess:
                pass
        
        try:
            if parent.is_running():
                parent.kill()
        except psutil.NoSuchProcess:
            pass
            
    except psutil.NoSuchProcess:
        pass


def run_api_server():
    """Run the FastAPI server"""
    print("🚀 Starting API server...")
    api_process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.api:app",
            "--host",
            "0.0.0.0",
            "--port",
            "3001",
            "--reload",
        ],
        cwd=Path(__file__).parent,
    )
    return api_process


def check_node_installed():
    """Check if Node.js is installed"""
    try:
        subprocess.run(["node", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_pnpm_installed():
    """Check if pnpm is installed"""
    try:
        subprocess.run(["pnpm", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_frontend_dependencies():
    """Install frontend dependencies if needed"""
    frontend_dir = Path(__file__).parent / "frontend"
    
    if not (frontend_dir / "node_modules").exists():
        print("📦 Installing frontend dependencies...")
        
        # Check if pnpm is available, otherwise use npm
        if check_pnpm_installed():
            subprocess.run(["pnpm", "install"], cwd=frontend_dir, check=True)
            print("✅ Frontend dependencies installed with pnpm")
        else:
            subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
            print("✅ Frontend dependencies installed with npm")


def run_nextjs_app():
    """Run the Next.js app"""
    print("🎨 Starting Next.js app...")
    
    frontend_dir = Path(__file__).parent / "frontend"
    
    # Check if Node.js is installed
    if not check_node_installed():
        print("❌ Node.js is not installed. Please install Node.js first.")
        print("You can download it from: https://nodejs.org/")
        return None
    
    # Install dependencies if needed
    install_frontend_dependencies()
    
    # Start Next.js development server
    if check_pnpm_installed():
        nextjs_process = subprocess.Popen(
            ["pnpm", "dev"],
            cwd=frontend_dir,
        )
    else:
        nextjs_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=frontend_dir,
        )
    
    return nextjs_process


def cleanup_processes(api_process, nextjs_process, redis_process):
    """Clean up processes properly"""
    print("\n🛑 Stopping services...")
    
    # Kill API server
    if api_process and api_process.poll() is None:
        print("🔄 Terminating API server...")
        kill_process_tree(api_process.pid)
    
    # Kill Next.js app
    if nextjs_process and nextjs_process.poll() is None:
        print("🔄 Terminating Next.js app...")
        kill_process_tree(nextjs_process.pid)
    
    # Stop Redis
    stop_redis(redis_process)
    
    # Additional cleanup for common ports
    try:
        # Kill processes on common ports
        for port in [3001, 3000, 6379]:  # 3000 is Next.js default port
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                try:
                    for conn in proc.info['connections']:
                        if conn.laddr.port == port:
                            print(f"🔄 Killing process on port {port}: {proc.info['name']}")
                            kill_process_tree(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
    except Exception as e:
        print(f"⚠️ Warning during cleanup: {e}")
    
    print("✅ Services stopped")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n🛑 Received interrupt signal, shutting down...")
    sys.exit(0)


def main():
    print("🎯 Starting RAG Chatbot Application (Next.js)")
    print("=" * 50)

    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    api_process = None
    nextjs_process = None
    redis_process = None

    try:
        # Start Redis first
        redis_process = start_redis()
        
        # Wait a bit for Redis to start if we started it
        if redis_process:
            print("⏳ Waiting for Redis to start...")
            time.sleep(3)
        
        # Verify Redis is running
        if not is_redis_running():
            print("❌ Redis is not running. Please start Redis manually and try again.")
            print("You can start Redis using:")
            print("  - redis-server")
            print("  - docker run -d -p 6379:6379 redis:alpine")
            print("  - brew services start redis")
            return

        # Start API server
        api_process = run_api_server()

        # Wait a bit for API to start
        print("⏳ Waiting for API server to start...")
        time.sleep(5)

        # Start Next.js app
        nextjs_process = run_nextjs_app()

        print("\n✅ All services are starting...")
        print("🌐 Next.js app will be available at: http://localhost:3000")
        print("🔗 API server will be available at: http://localhost:3001")
        print("🔴 Redis server is running at: localhost:6379")
        print("\n🛑 Press Ctrl+C to stop all services")

        # Wait for both processes
        while True:
            if api_process and api_process.poll() is not None:
                print("❌ API server stopped unexpectedly")
                break
            if nextjs_process and nextjs_process.poll() is not None:
                print("❌ Next.js app stopped unexpectedly")
                break
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Keyboard interrupt received")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        cleanup_processes(api_process, nextjs_process, redis_process)


if __name__ == "__main__":
    main() 