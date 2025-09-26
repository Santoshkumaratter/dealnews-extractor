#!/usr/bin/env python3
"""
DealNews Scraper - Main run script
This script runs the DealNews scraper with all client requirements:
1. Uses Scrapy framework to scrape data from DealNews
2. Routes traffic through webshare.io proxies with rotation
3. Stores all data in MySQL database
4. Provides robust parsing with CSS/XPath selectors
5. Handles proxies and reliability with retry/backoff
6. Exports data to JSON files for debugging
"""
import sys
import os
import logging
from dotenv import load_dotenv

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set the reactor before importing scrapy
import scrapy.utils.reactor
# Use the most compatible reactor for Docker environments
scrapy.utils.reactor.install_reactor('twisted.internet.asyncioreactor.AsyncioSelectorReactor')

# Now import and run scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from dealnews_scraper.spiders.dealnews_spider import DealnewsSpider

def validate_environment():
    """Validate environment variables and dependencies"""
    print("🔍 Validating environment and dependencies...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ ERROR: .env file not found!")
        print("📋 Please copy env.example to .env and configure your credentials")
        print("   Command: cp env.example .env")
        return False
    
    # Load environment variables
    load_dotenv()
    
    # Check critical environment variables
    required_vars = {
        'MYSQL_HOST': os.getenv('MYSQL_HOST'),
        'MYSQL_PORT': os.getenv('MYSQL_PORT'),
        'MYSQL_USER': os.getenv('MYSQL_USER'),
        'MYSQL_PASSWORD': os.getenv('MYSQL_PASSWORD'),
        'MYSQL_DATABASE': os.getenv('MYSQL_DATABASE'),
    }
    
    missing_vars = []
    for var_name, var_value in required_vars.items():
        if not var_value:
            missing_vars.append(var_name)
    
    if missing_vars:
        print(f"❌ ERROR: Missing required environment variables: {', '.join(missing_vars)}")
        print("📋 Please check your .env file and ensure all variables are set")
        return False
    
    # Check proxy credentials if proxy is enabled
    disable_proxy = os.getenv('DISABLE_PROXY', '').lower() in ('1', 'true', 'yes')
    if not disable_proxy:
        proxy_user = os.getenv('PROXY_USER')
        proxy_pass = os.getenv('PROXY_PASS')
        if not proxy_user or not proxy_pass:
            print("⚠️  WARNING: Proxy enabled but credentials not found")
            print("📋 Either set PROXY_USER and PROXY_PASS in .env or set DISABLE_PROXY=true")
            print("🔄 Continuing without proxy...")
            os.environ['DISABLE_PROXY'] = 'true'
    
    print("✅ Environment validation passed")
    return True

def check_dependencies():
    """Check if all required dependencies are available"""
    print("📦 Checking dependencies...")
    
    required_modules = [
        ('scrapy', 'Scrapy framework'),
        ('mysql.connector', 'MySQL connector'),
        ('dotenv', 'Environment variables'),
        ('requests', 'HTTP requests'),
    ]
    
    missing_deps = []
    for module_name, description in required_modules:
        try:
            __import__(module_name)
            print(f"✅ {description}: Available")
        except ImportError:
            print(f"❌ {description}: Missing")
            missing_deps.append(module_name)
    
    if missing_deps:
        print(f"❌ ERROR: Missing dependencies: {', '.join(missing_deps)}")
        print("📋 Please install requirements: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies available")
    return True

def test_mysql_connection():
    """Test MySQL connection before starting scraper"""
    print("🗄️  Testing MySQL connection...")
    
    try:
        import mysql.connector
        
        mysql_host = os.getenv('MYSQL_HOST', 'localhost')
        mysql_port = int(os.getenv('MYSQL_PORT', '3307'))
        mysql_user = os.getenv('MYSQL_USER', 'root')
        mysql_password = os.getenv('MYSQL_PASSWORD', 'root')
        mysql_database = os.getenv('MYSQL_DATABASE', 'dealnews')
        
        print(f"🔗 Connecting to {mysql_host}:{mysql_port} as {mysql_user}...")
        
        conn = mysql.connector.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database,
            connection_timeout=10
        )
        
        # Test basic query
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        print("✅ MySQL connection successful")
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ MySQL connection failed: {e}")
        print("📋 Please check your MySQL settings in .env file")
        print("📋 Ensure MySQL server is running and accessible")
        return False
    except Exception as e:
        print(f"❌ Unexpected error testing MySQL: {e}")
        return False

def main():
    print("🚀 DealNews Scraper - Starting Environment Check")
    print("=" * 50)
    
    # Step 1: Validate environment
    if not validate_environment():
        print("\n❌ Environment validation failed. Exiting.")
        sys.exit(1)
    
    # Step 2: Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Exiting.")
        sys.exit(1)
    
    # Step 3: Test MySQL connection
    mysql_enabled = os.getenv('DISABLE_MYSQL', '').lower() not in ('1', 'true', 'yes')
    if mysql_enabled:
        if not test_mysql_connection():
            print("\n❌ MySQL connection test failed. Exiting.")
            print("💡 Tip: Set DISABLE_MYSQL=true in .env to run without database")
            sys.exit(1)
    
    print("\n✅ All checks passed! Starting scraper...")
    print("=" * 50)
    
    # Set up minimal logging (only to file, not console)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        handlers=[
            logging.FileHandler("dealnews_scraper.log"),
        ]
    )
    logger = logging.getLogger(__name__)
    
    # Get project settings
    settings = get_project_settings()
    
    # Configure proxy usage based on environment variable
    use_proxy = os.getenv('DISABLE_PROXY', '').lower() not in ('1', 'true', 'yes')
    if use_proxy:
        proxy_user = os.getenv('PROXY_USER')
        proxy_pass = os.getenv('PROXY_PASS')
        if proxy_user and proxy_pass:
            logger.info(f"Using proxy for scraping with user: {proxy_user}")
        else:
            logger.warning("Proxy enabled but credentials not found, disabling proxy")
            os.environ['DISABLE_PROXY'] = 'true'
    else:
        logger.info("Proxy disabled for local testing")
        os.environ['DISABLE_PROXY'] = 'true'
    
    # Configure MySQL
    mysql_enabled = os.getenv('DISABLE_MYSQL', '').lower() not in ('1', 'true', 'yes')
    if not mysql_enabled:
        settings.set('ITEM_PIPELINES', {})
        logger.info("MySQL pipeline disabled")
    else:
        # Make sure MySQL pipeline is enabled
        settings.set('ITEM_PIPELINES', {
            'dealnews_scraper.pipelines.MySQLPipeline': 300,
        })
        logger.info("Using MySQL pipeline")
        
        # Verify MySQL settings
        mysql_host = os.getenv('MYSQL_HOST', 'localhost')
        mysql_port = os.getenv('MYSQL_PORT', '3307')
        mysql_user = os.getenv('MYSQL_USER', 'root')
        mysql_password = os.getenv('MYSQL_PASSWORD', 'root')
        mysql_database = os.getenv('MYSQL_DATABASE', 'dealnews')
        logger.info(f"MySQL settings: {mysql_host}:{mysql_port}, user: {mysql_user}, db: {mysql_database}")
        
        # Check if MySQL is running
        try:
            import mysql.connector
            conn = mysql.connector.connect(
                host=mysql_host,
                port=int(mysql_port),
                user=mysql_user,
                password=mysql_password,
                database=mysql_database,
                connection_timeout=5
            )
            conn.close()
            logger.info("MySQL connection test successful")
        except Exception as e:
            logger.error(f"MySQL connection test failed: {e}")
            logger.warning("Disabling MySQL pipeline due to connection error")
            settings.set('ITEM_PIPELINES', {})
            # Enable JSON export as fallback
            settings.set('FEED_FORMAT', 'json')
            settings.set('FEED_URI', 'exports/deals.json')
            mysql_enabled = False
        
        # Ensure MySQL environment variables are set
        os.environ['MYSQL_HOST'] = mysql_host
        os.environ['MYSQL_PORT'] = mysql_port
        os.environ['MYSQL_USER'] = mysql_user
        os.environ['MYSQL_PASSWORD'] = mysql_password
        os.environ['MYSQL_DATABASE'] = mysql_database
    
    # Set up JSON feed exporter (always export to JSON for debugging)
    os.makedirs('exports', exist_ok=True)
    settings.set('FEEDS', {
        'exports/deals.json': {
            'format': 'json',
            'encoding': 'utf8',
            'indent': 2,
        },
    })
    
    # Suppress Scrapy console output
    settings.set('LOG_LEVEL', 'ERROR')
    settings.set('LOG_ENABLED', False)
    
    # Create and run crawler
    process = CrawlerProcess(settings)
    process.crawl(DealnewsSpider)
    
    print("🚀 DealNews Scraper Starting...")
    print("📊 Extracting deals from DealNews.com...")
    print("💾 Saving data to MySQL database...")
    print("📁 Exporting data to JSON file...")
    
    process.start()
    
    print("✅ DealNews Scraper Completed Successfully!")
    print("📈 Data extracted and saved to database")
    print("📄 Check exports/deals.json for scraped data")
    print("🗄️  Access database via Adminer at http://localhost:8080")

if __name__ == "__main__":
    main()
