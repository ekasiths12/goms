#!/usr/bin/env python3
"""
Comprehensive Server Restart Script for Garment Management System
This script kills any existing processes on ports 3000 and 8000, then starts both frontend and backend servers.
"""

import os
import sys
import subprocess
import signal
import time
import threading
from pathlib import Path

def kill_processes_on_ports():
    """Kill any processes running on ports 3000 and 8000"""
    print("🔫 Killing processes on ports 3000 and 8000...")
    
    ports = [3000, 8000]
    for port in ports:
        try:
            # Find processes using the port
            result = subprocess.run(['lsof', '-ti', f':{port}'], 
                                  capture_output=True, text=True, check=False)
            
            if result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        try:
                            print(f"   🎯 Killing process {pid} on port {port}")
                            os.kill(int(pid), signal.SIGKILL)
                        except (ValueError, ProcessLookupError) as e:
                            print(f"   ⚠️  Could not kill process {pid}: {e}")
                time.sleep(2)  # Give time for processes to terminate
            else:
                print(f"   ✅ No processes found on port {port}")
        except Exception as e:
            print(f"   ⚠️  Error checking port {port}: {e}")
    
    print("   ✅ Process cleanup completed")

def setup_environment():
    """Set up environment variables for local development"""
    env_vars = {
        'FLASK_DEBUG': 'True',
        'FLASK_ENV': 'development',
        'DATABASE_URL': 'mysql://GOMS:PGOMS@localhost/garment_db'
    }
    
    print("🔧 Setting up environment variables...")
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"   {key}={value}")

def start_backend_server():
    """Start the Flask backend server"""
    print("🚀 Starting Flask backend server...")
    print("📍 Backend will be available at: http://localhost:8000")
    
    backend_dir = Path(__file__).parent / 'backend'
    os.chdir(backend_dir)
    
    try:
        subprocess.run([sys.executable, 'main.py'], check=True)
    except KeyboardInterrupt:
        print("\n👋 Backend server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error starting backend server: {e}")
        return False
    
    return True

def start_frontend_server():
    """Start the frontend HTTP server"""
    print("🌐 Starting frontend server...")
    print("📍 Frontend will be available at: http://localhost:3000")
    
    frontend_dir = Path(__file__).parent / 'frontend'
    os.chdir(frontend_dir)
    
    try:
        subprocess.run([sys.executable, '-m', 'http.server', '3000'], check=True)
    except KeyboardInterrupt:
        print("\n👋 Frontend server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error starting frontend server: {e}")
        return False
    
    return True

def main():
    """Main function"""
    print("🏭 Garment Management System - Server Restart")
    print("=" * 60)
    
    # Kill existing processes
    kill_processes_on_ports()
    
    # Setup environment
    setup_environment()
    
    print("\n📋 Starting servers...")
    print("📍 Backend: http://localhost:8000")
    print("📍 Frontend: http://localhost:3000")
    print("📍 Dashboard: http://localhost:3000/dashboard.html")
    print("\n⏹️  Press Ctrl+C to stop all servers")
    print("-" * 60)
    
    # Start backend server in a separate thread
    backend_thread = threading.Thread(target=start_backend_server, daemon=True)
    backend_thread.start()
    
    # Wait a moment for backend to start
    time.sleep(3)
    
    # Start frontend server in main thread
    try:
        start_frontend_server()
    except KeyboardInterrupt:
        print("\n👋 All servers stopped by user")

if __name__ == '__main__':
    main()
