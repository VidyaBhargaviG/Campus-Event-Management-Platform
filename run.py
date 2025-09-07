#!/usr/bin/env python3
"""
Event Reporting System - Startup Script
Run this script to start the application
"""

import uvicorn
import sys
import os

def main():
    """Main function to start the application"""
    print("🚀 Starting Event Reporting System...")
    print("📊 Campus Event Management Platform")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("main.py"):
        print("❌ Error: main.py not found. Please run this script from the project root directory.")
        sys.exit(1)
    
    # Check if requirements are installed
    try:
        import fastapi
        import sqlalchemy
        print("✅ Dependencies check passed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)
    
    print("\n🌐 Starting server...")
    print("📍 Web Interface: http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("❤️  Health Check: http://localhost:8000/health")
    print("\n💡 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Start the server
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,  # Auto-reload on code changes
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Goodbye!")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

