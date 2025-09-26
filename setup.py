#!/usr/bin/env python3
"""
DealNews Scraper Setup Script
This script helps you set up the DealNews scraper quickly and easily.
"""

import os
import subprocess
import sys

def print_header():
    print("=" * 60)
    print(" DealNews Scraper Setup")
    print("=" * 60)
    print()

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print(" Python 3.7+ is required. Current version:", sys.version)
        return False
    print(f"Python version: {sys.version.split()[0]}")
    return True

def install_requirements():
    """Install Python requirements"""
    print("Installing Python requirements...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print(" Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError:
        print(" Failed to install requirements")
        return False

def create_env_file():
    """Create .env file from template"""
    if os.path.exists('.env'):
        print(" .env file already exists")
        return True
    
    if os.path.exists('env.example'):
        try:
            with open('env.example', 'r') as src, open('.env', 'w') as dst:
                dst.write(src.read())
            print("Created .env file from template")
            print(" Please edit .env file with your credentials")
            return True
        except Exception as e:
            print(f" Failed to create .env file: {e}")
            return False
    else:
        print(" env.example file not found")
        return False

def check_mysql():
    """Check if MySQL is available"""
    try:
        import mysql.connector
        print("MySQL connector available")
        return True
    except ImportError:
        print("MySQL connector not installed (will be installed with requirements)")
        return False

def main():
    print_header()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Create .env file
    if not create_env_file():
        sys.exit(1)
    
    # Check MySQL
    check_mysql()
    
    print()
    print("🎉 Setup completed successfully!")
    print()
    print("Next steps:")
    print("1. Edit .env file with your credentials")
    print("2. Setup MySQL database (see README.md)")
    print("3. Run: python run.py")
    print()
    print("For Docker setup:")
    print("1. Edit .env file with your credentials")
    print("2. Run: docker-compose up")
    print()
    print("See README.md for detailed instructions")

if __name__ == "__main__":
    main()
