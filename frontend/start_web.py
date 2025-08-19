#!/usr/bin/env python3
"""
Start script for the Voice Note Parser Web Interface
"""

import os
import sys
import subprocess
import time

# Ensure we're in the web directory
web_dir = os.path.dirname(os.path.abspath(__file__))
if os.getcwd() != web_dir:
    print(f"📁 Changing to web directory: {web_dir}")
    os.chdir(web_dir)

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def kill_processes_on_port(port):
    """Kill all processes running on the specified port, excluding the current process."""
    try:
        current_pid = os.getpid()
        
        # Find processes using the port
        if sys.platform == "darwin":  # macOS
            cmd = f"lsof -ti:{port}"
        else:  # Linux/Unix
            cmd = f"lsof -ti:{port}"
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            external_pids = [pid.strip() for pid in pids if pid.strip() and int(pid.strip()) != current_pid]
            
            if external_pids:
                print(f"🔴 Found {len(external_pids)} external process(es) running on port {port}")
                
                for pid in external_pids:
                    try:
                        subprocess.run(f"kill -9 {pid}", shell=True, check=True)
                        print(f"   ✅ Killed external process {pid}")
                    except subprocess.CalledProcessError:
                        print(f"   ⚠️  Failed to kill process {pid}")
                
                # Wait a moment for processes to fully terminate
                time.sleep(1)
                print(f"✅ All external processes on port {port} have been terminated")
            else:
                print(f"✅ Only current process ({current_pid}) found on port {port}")
        else:
            print(f"✅ No processes found running on port {port}")
            
    except Exception as e:
        print(f"⚠️  Warning: Could not check for processes on port {port}: {e}")

if __name__ == '__main__':
    PORT = 5001  # Back to original port
    print("🚀 Starting Voice Note Parser Web Interface...")
    print("=" * 50)
    print(f"📁 Working directory: {os.getcwd()}")
    
    # Kill any existing processes on the port
    print(f"🔍 Checking for existing processes on port {PORT}...")
    kill_processes_on_port(PORT)
    
    print(f"\n🚀 Launching web application on port {PORT}...")
    print(f"📱 Open your browser and go to: http://localhost:{PORT}")
    print("⏹️  Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        from app import app
        # Disable debug mode to prevent auto-reload issues
        app.run(debug=False, host='0.0.0.0', port=PORT)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)
