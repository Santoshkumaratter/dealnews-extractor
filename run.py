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
scrapy.utils.reactor.install_reactor('twisted.internet.selectreactor.SelectReactor')

# Monkey patch to fix _handleSignals issue
import twisted.internet.reactor
if not hasattr(twisted.internet.reactor, '_handleSignals'):
    twisted.internet.reactor._handleSignals = lambda: None

# Now import and run scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from dealnews_scraper.spiders.dealnews_spider import DealnewsSpider

def main():
    # Load environment variables
    load_dotenv()
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        handlers=[
            logging.FileHandler("dealnews_scraper.log"),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    
    # Get project settings
    settings = get_project_settings()
    
    # Configure proxy usage based on environment variable
    use_proxy = os.getenv('DISABLE_PROXY', '').lower() not in ('1', 'true', 'yes')
    if use_proxy:
        logger.info("Using proxy for scraping")
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
    
    # Create and run crawler
    process = CrawlerProcess(settings)
    process.crawl(DealnewsSpider)
    
    logger.info("Starting DealNews scraper")
    process.start()
    
    logger.info("Scraper run completed!")

if __name__ == "__main__":
    main()
