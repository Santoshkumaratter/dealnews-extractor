#!/usr/bin/env python3
"""
Setup script to create the DealNews database and table in Laradock MySQL
Run this once before running the scraper
"""

import mysql.connector
import os
from dotenv import load_dotenv

def setup_database():
    """Create database and table in Laradock MySQL"""
    
    # Load environment variables
    load_dotenv()
    
    # Database connection parameters
    config = {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', 'root'),
        'autocommit': True
    }
    
    try:
        print("🔗 Connecting to Laradock MySQL...")
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        print("✅ Connected to Laradock MySQL successfully!")
        
        # Create database
        database_name = os.getenv('MYSQL_DATABASE', 'dealnews')
        print(f"📊 Creating database '{database_name}'...")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name}")
        print(f"✅ Database '{database_name}' created/verified!")
        
        # Use the database
        cursor.execute(f"USE {database_name}")
        
        # Create table
        print("📋 Creating deals table...")
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS deals (
            id INT AUTO_INCREMENT PRIMARY KEY,
            dealid VARCHAR(50) UNIQUE,
            recid VARCHAR(50),
            url TEXT,
            title TEXT,
            price VARCHAR(100),
            promo TEXT,
            category VARCHAR(100),
            store VARCHAR(100),
            deal TEXT,
            dealplus TEXT,
            deallink TEXT,
            dealtext TEXT,
            dealhover TEXT,
            published VARCHAR(100),
            popularity VARCHAR(50),
            staffpick VARCHAR(10),
            detail TEXT,
            raw_html LONGTEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_dealid (dealid),
            INDEX idx_store (store),
            INDEX idx_category (category),
            INDEX idx_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        
        cursor.execute(create_table_sql)
        print("✅ Deals table created/verified!")
        
        # Check if table exists and show structure
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"📊 Available tables: {[table[0] for table in tables]}")
        
        cursor.execute("DESCRIBE deals")
        columns = cursor.fetchall()
        print(f"📋 Deals table has {len(columns)} columns")
        
        print("\n🎉 Database setup completed successfully!")
        print(f"📊 Database: {database_name}")
        print(f"🔗 Host: {config['host']}:{config['port']}")
        print(f"👤 User: {config['user']}")
        
    except mysql.connector.Error as err:
        print(f"❌ MySQL Error: {err}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("🔌 Database connection closed")
    
    return True

if __name__ == "__main__":
    print("🚀 DealNews Database Setup for Laradock")
    print("=" * 50)
    
    success = setup_database()
    
    if success:
        print("\n✅ Setup completed! You can now run:")
        print("   docker-compose up scraper")
    else:
        print("\n❌ Setup failed! Please check your Laradock MySQL connection.")
        exit(1)
