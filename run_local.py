#!/usr/bin/env python3
"""
Local Development Server for Garment Management System
Run this script to start the Flask backend locally for testing.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    required_packages = [
        'flask',
        'flask-sqlalchemy', 
        'flask-cors',
        'pymysql',
        'dotenv'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n📦 Install them with:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ All required packages are installed")
    return True

def setup_environment():
    """Set up environment variables for local development"""
    env_vars = {
        'FLASK_DEBUG': 'True',
        'FLASK_ENV': 'development',
        'DATABASE_URL': 'mysql://GOMS:PGOMS@localhost/garment_db'
    }
    
    print("🔧 Setting up environment variables for local development...")
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"   {key}={value}")
    
    # Create local storage directories
    print("📁 Setting up local storage directories...")
    backend_dir = Path(__file__).parent / 'backend'
    static_dir = backend_dir / 'static' / 'uploads'
    
    # Create directories
    (static_dir / 'images').mkdir(parents=True, exist_ok=True)
    (static_dir / 'uploads').mkdir(parents=True, exist_ok=True)
    (static_dir / 'pdfs').mkdir(parents=True, exist_ok=True)
    
    print(f"   ✅ Local storage ready at: {static_dir}")

def start_server():
    """Start the Flask development server"""
    print("\n🚀 Starting Flask development server...")
    print("📍 Backend will be available at: http://localhost:8000")
    print("📍 Frontend files are in the 'frontend' directory")
    print("📍 Health check: http://localhost:8000/api/health")
    print("📍 Test endpoint: http://localhost:8000/test")
    print("\n💡 To test the frontend:")
    print("   1. Open frontend/fabric-invoices.html in your browser")
    print("   2. Or serve the frontend directory with a local server")
    print("\n⏹️  Press Ctrl+C to stop the server")
    print("-" * 60)
    
    # Change to backend directory and run Flask app
    backend_dir = Path(__file__).parent / 'backend'
    os.chdir(backend_dir)
    
    try:
        # Run the Flask app
        subprocess.run([sys.executable, 'main.py'], check=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error starting server: {e}")
        return False
    
    return True

def main():
    """Main function"""
    print("🏭 Garment Management System - Local Development")
    print("=" * 60)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Setup environment
    setup_environment()
    
    # Start server
    start_server()

if __name__ == '__main__':
    main()
