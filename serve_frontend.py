#!/usr/bin/env python3
"""
Simple HTTP Server for Frontend Files
Run this to serve the frontend HTML files locally for testing.
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

def start_frontend_server():
    """Start a simple HTTP server to serve frontend files"""
    frontend_dir = Path(__file__).parent / 'frontend'
    
    if not frontend_dir.exists():
        print("❌ Frontend directory not found!")
        return False
    
    # Change to frontend directory
    os.chdir(frontend_dir)
    
    PORT = 3000
    
    print("🌐 Starting frontend server...")
    print(f"📍 Frontend will be available at: http://localhost:{PORT}")
    print(f"📍 Serving files from: {frontend_dir}")
    print("\n📄 Available pages:")
    print(f"   - http://localhost:{PORT}/fabric-invoices.html")
    print(f"   - http://localhost:{PORT}/stitching-records.html")
    print(f"   - http://localhost:{PORT}/packing-lists.html")
    print(f"   - http://localhost:{PORT}/group-bills.html")
    print(f"   - http://localhost:{PORT}/index.html")
    print("\n💡 Make sure the Flask backend is running on port 8000")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 60)
    
    try:
        with socketserver.TCPServer(("", PORT), http.server.SimpleHTTPRequestHandler) as httpd:
            print(f"🚀 Server started at http://localhost:{PORT}")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Frontend server stopped by user")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {PORT} is already in use. Try a different port or stop the existing server.")
        else:
            print(f"❌ Error starting server: {e}")
        return False
    
    return True

if __name__ == '__main__':
    start_frontend_server()
