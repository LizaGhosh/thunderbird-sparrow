#!/usr/bin/env python3
"""
Launcher script for Voice Note Parser Web Interface
Automatically changes to web directory and starts the application
"""

import os
import sys
import subprocess

def main():
    # Get the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    web_dir = os.path.join(project_root, 'frontend')
    
    print("🚀 Launching Voice Note Parser Web Interface...")
    print(f"📁 Project root: {project_root}")
    print(f"📁 Web directory: {web_dir}")
    print("=" * 50)
    
    # Change to web directory
    os.chdir(web_dir)
    print(f"✅ Changed to web directory: {os.getcwd()}")
    
    # Start the web application
    try:
        subprocess.run([sys.executable, 'start_web.py'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting web application: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Web application stopped by user")

if __name__ == '__main__':
    main()
