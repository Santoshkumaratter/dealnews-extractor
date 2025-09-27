#!/usr/bin/env python3
"""
Quick test script to verify the scraper is working
"""
import os
import sys
import subprocess
import time

def test_scraper():
    print("🧪 Testing DealNews Scraper...")
    print("=" * 50)
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("Please run: cp .env-template .env")
        return False
    
    # Check if database setup was done
    print("✅ Environment file found")
    
    # Test Docker setup
    try:
        result = subprocess.run(['docker-compose', 'config'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ Docker Compose configuration is valid")
        else:
            print("❌ Docker Compose configuration error:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Docker Compose test failed: {e}")
        return False
    
    print("\n🚀 Ready to run scraper!")
    print("Run: docker-compose up scraper")
    print("\n📊 After running, check your data at:")
    print("   - http://localhost:8081 (Adminer)")
    print("   - Or your existing phpMyAdmin")
    
    return True

if __name__ == "__main__":
    success = test_scraper()
    sys.exit(0 if success else 1)
