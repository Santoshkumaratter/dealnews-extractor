import os
import mysql.connector
import logging
from dealnews_scraper.items import DealnewsItem, DealImageItem, DealCategoryItem, RelatedDealItem

class MySQLPipeline:
    """Pipeline for storing scraped items in MySQL database.
    If MySQL connection fails, data will be saved to JSON files as a fallback.
    """
    def open_spider(self, spider):
        try:
            # Check if MySQL is disabled
            disable_mysql = os.getenv('DISABLE_MYSQL', 'false').lower() in ('1', 'true', 'yes')
            if disable_mysql:
                logging.info("MySQL pipeline disabled by DISABLE_MYSQL flag")
                spider.logger.info("MySQL pipeline disabled by DISABLE_MYSQL flag")
                self.mysql_enabled = False
                return
            
            self.mysql_enabled = True
            spider.logger.info("MySQL pipeline enabled - attempting connection...")
            self.save_html_snapshots = os.getenv('SAVE_HTML_SNAPSHOTS', 'false').lower() in ('1', 'true', 'yes')
            self.snapshots_dir = os.getenv('SNAPSHOTS_DIR', 'exports/html_snapshots')
            if self.save_html_snapshots and not os.path.isdir(self.snapshots_dir):
                os.makedirs(self.snapshots_dir, exist_ok=True)

            # Get MySQL connection settings from environment or use defaults
            mysql_host = os.getenv('MYSQL_HOST', 'localhost')
            mysql_port = int(os.getenv('MYSQL_PORT', '3307'))  # Use port 3307 as default
            mysql_user = os.getenv('MYSQL_USER', 'root')  # Use root user by default
            mysql_password = os.getenv('MYSQL_PASSWORD', 'root')  # Use root password by default
            mysql_database = os.getenv('MYSQL_DATABASE', 'dealnews')
            
            # Log the connection details for debugging
            logging.info(f"Connecting to MySQL: {mysql_host}:{mysql_port} as {mysql_user} to database {mysql_database}")
            spider.logger.info(f"Connecting to MySQL: {mysql_host}:{mysql_port} as {mysql_user} to database {mysql_database}")
            
            try:
                self.conn = mysql.connector.connect(
                    host=mysql_host,
                    port=mysql_port,
                    user=mysql_user,
                    password=mysql_password,
                    database=mysql_database,
                    # Additional connection parameters for reliability
                    use_pure=True,  # Use the pure Python implementation
                    connection_timeout=30,
                    autocommit=True
                )
                logging.info("MySQL connection successful")
                spider.logger.info("MySQL connection successful")
            except mysql.connector.Error as err:
                logging.error(f"MySQL connection error: {err}")
                spider.logger.error(f"MySQL connection error: {err}")
                # Try alternative connection without specifying port
                try:
                    logging.info("Trying alternative connection without port specification...")
                    spider.logger.info("Trying alternative connection without port specification...")
                    self.conn = mysql.connector.connect(
                        host=mysql_host,
                        user=mysql_user,
                        password=mysql_password,
                        database=mysql_database,
                        use_pure=True,
                        connection_timeout=30,
                        autocommit=True
                    )
                    logging.info("Alternative MySQL connection successful")
                    spider.logger.info("Alternative MySQL connection successful")
                except mysql.connector.Error as err2:
                    logging.error(f"Alternative MySQL connection also failed: {err2}")
                    spider.logger.error(f"Alternative MySQL connection also failed: {err2}")
                    spider.logger.error("MySQL pipeline will be disabled - data will be saved to JSON only")
                    self.mysql_enabled = False
                    return
            
            self.cursor = self.conn.cursor()
            
            # Create main deals table with all fields from PDF requirements
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS deals (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    dealid VARCHAR(100),
                    recid VARCHAR(100),
                    url VARCHAR(500) UNIQUE,
                    title TEXT,
                    price VARCHAR(100),
                    promo VARCHAR(255),
                    category VARCHAR(100),
                    store VARCHAR(100),
                    deal VARCHAR(255),
                    dealplus VARCHAR(255),
                    deallink VARCHAR(500),
                    dealtext VARCHAR(255),
                    dealhover VARCHAR(255),
                    published VARCHAR(100),
                    popularity VARCHAR(50),
                    staffpick VARCHAR(50),
                    detail TEXT,
                    raw_html TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    
                    INDEX idx_dealid (dealid),
                    INDEX idx_category (category),
                    INDEX idx_store (store),
                    INDEX idx_created_at (created_at),
                    INDEX idx_price (price(20))
                )
            """)
            
            # Create deal images table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS deal_images (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    dealid VARCHAR(100),
                    imageurl VARCHAR(500),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_dealid (dealid)
                )
            """)
            
            # Create deal categories table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS deal_categories (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    dealid VARCHAR(100),
                    category_name VARCHAR(100),
                    category_url VARCHAR(500),
                    category_title VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_dealid (dealid)
                )
            """)
            
            # Create related deals table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS related_deals (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    dealid VARCHAR(100),
                    relatedurl VARCHAR(500),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_dealid (dealid)
                )
            """)
            
            self.conn.commit()
            logging.info("MySQL connection established and all tables ensured.")
        except mysql.connector.Error as err:
            logging.error(f"MySQL connection error: {err}")
            raise

    def process_item(self, item, spider):
        try:
            # Skip processing if MySQL is disabled
            if not getattr(self, 'mysql_enabled', True):
                return item
                
            if isinstance(item, DealnewsItem):
                # Validate minimal fields to avoid inserting broken rows
                if not item.get('url'):
                    logging.warning('Skipping deal with missing url')
                    return item
                if not item.get('title') and not item.get('price'):
                    logging.warning(f"Skipping deal missing title/price: {item.get('url')}")
                    return item
                
                # Save HTML snapshot if enabled
                if self.save_html_snapshots:
                    self._persist_html_snapshot(item)
                
                # Process the main deal item
                try:
                    self.process_deal_item(item, spider)
                except mysql.connector.Error as err:
                    if err.errno == 1062:  # Duplicate entry error
                        logging.info(f"Deal already exists (duplicate): {item.get('url')}")
                    else:
                        # Try to reconnect if connection lost
                        if err.errno == 2006:  # MySQL server has gone away
                            logging.warning("MySQL connection lost, attempting to reconnect...")
                            self._reconnect()
                            # Try again after reconnection
                            self.process_deal_item(item, spider)
                        else:
                            logging.error(f"MySQL error processing deal: {err}")
                            raise
            
            # Process related items
            elif isinstance(item, DealImageItem):
                try:
                    self.process_image_item(item, spider)
                except mysql.connector.Error as err:
                    logging.error(f"Error inserting image: {err}")
            
            elif isinstance(item, DealCategoryItem):
                try:
                    self.process_category_item(item, spider)
                except mysql.connector.Error as err:
                    logging.error(f"Error inserting category: {err}")
            
            elif isinstance(item, RelatedDealItem):
                try:
                    self.process_related_item(item, spider)
                except mysql.connector.Error as err:
                    logging.error(f"Error inserting related deal: {err}")
        
        except Exception as e:
            logging.error(f"Unexpected error processing item: {e}")
        
        return item
        
    def _reconnect(self):
        """Reconnect to MySQL if connection is lost"""
        try:
            if hasattr(self, 'conn') and self.conn:
                self.conn.close()
            
            # Get MySQL connection settings from environment
            mysql_host = os.getenv('MYSQL_HOST', 'localhost')
            mysql_port = int(os.getenv('MYSQL_PORT', '3307'))
            mysql_user = os.getenv('MYSQL_USER', 'root')
            mysql_password = os.getenv('MYSQL_PASSWORD', 'root')
            mysql_database = os.getenv('MYSQL_DATABASE', 'dealnews')
            
            logging.info(f"Reconnecting to MySQL: {mysql_host}:{mysql_port}")
            self.conn = mysql.connector.connect(
                host=mysql_host,
                port=mysql_port,
                user=mysql_user,
                password=mysql_password,
                database=mysql_database,
                use_pure=True,
                connection_timeout=30,
                autocommit=True
            )
            self.cursor = self.conn.cursor()
            logging.info("MySQL reconnection successful")
        except mysql.connector.Error as err:
            logging.error(f"Failed to reconnect to MySQL: {err}")
            raise

    def _persist_html_snapshot(self, item: DealnewsItem):
        try:
            url = item.get('url', 'unknown')
            # build deterministic filename
            safe_name = (
                url.replace('https://', '').replace('http://', '').replace('/', '_')
            )
            if len(safe_name) > 140:
                safe_name = safe_name[:140]
            filename = os.path.join(self.snapshots_dir, f"{safe_name}.html")
            raw_html = item.get('raw_html', '') or ''
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(raw_html)
            logging.info(f"Saved HTML snapshot: {filename}")
        except Exception as e:
            logging.warning(f"Failed to save HTML snapshot: {e}")

    def process_deal_item(self, item, spider):
        """Process main deal item with deduplication"""
        deal_url = item.get('url', '')
        deal_title = item.get('title', 'Unknown')[:50]
        
        # Check if deal already exists by URL (deduplication)
        self.cursor.execute("SELECT id, title FROM deals WHERE url=%s", (deal_url,))
        existing_deal = self.cursor.fetchone()
        
        if existing_deal:
            spider.logger.info(f"🔄 DUPLICATE SKIPPED: Deal already exists (ID: {existing_deal[0]}) - {deal_title}")
            logging.info(f"Deal already exists, skipping: {deal_url}")
            return
        
        # Insert new deal
        try:
            self.cursor.execute("""
                INSERT INTO deals (
                    dealid, recid, url, title, price, promo, category, store,
                    deal, dealplus, deallink, dealtext, dealhover, published,
                    popularity, staffpick, detail, raw_html
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                item.get('dealid', ''),
                item.get('recid', ''),
                item.get('url', ''),
                item.get('title', ''),
                item.get('price', ''),
                item.get('promo', ''),
                item.get('category', ''),
                item.get('store', ''),
                item.get('deal', ''),
                item.get('dealplus', ''),
                item.get('deallink', ''),
                item.get('dealtext', ''),
                item.get('dealhover', ''),
                item.get('published', ''),
                item.get('popularity', ''),
                item.get('staffpick', ''),
                item.get('detail', ''),
                item.get('raw_html', '')
            ))
            self.conn.commit()
            spider.logger.info(f"✅ NEW DEAL SAVED: {deal_title}")
            logging.info(f"Inserted deal: {deal_title}")
        except mysql.connector.Error as err:
            if err.errno == 1062:  # Duplicate entry error (race condition)
                spider.logger.info(f"🔄 DUPLICATE SKIPPED: Deal was inserted by another process - {deal_title}")
                logging.info(f"Deal was inserted by another process, skipping: {deal_url}")
            else:
                raise

    def process_image_item(self, item, spider):
        """Process deal image item"""
        self.cursor.execute("""
            INSERT INTO deal_images (dealid, imageurl) VALUES (%s, %s)
        """, (
            item.get('dealid', ''),
            item.get('imageurl', '')
        ))
        self.conn.commit()
        logging.info(f"Inserted image for deal {item.get('dealid', '')}")

    def process_category_item(self, item, spider):
        """Process deal category item"""
        self.cursor.execute("""
            INSERT INTO deal_categories (dealid, category_name, category_url, category_title) 
            VALUES (%s, %s, %s, %s)
        """, (
            item.get('dealid', ''),
            item.get('category_name', ''),
            item.get('category_url', ''),
            item.get('category_title', '')
        ))
        self.conn.commit()
        logging.info(f"Inserted category for deal {item.get('dealid', '')}")

    def process_related_item(self, item, spider):
        """Process related deal item"""
        self.cursor.execute("""
            INSERT INTO related_deals (dealid, relatedurl) VALUES (%s, %s)
        """, (
            item.get('dealid', ''),
            item.get('relatedurl', '')
        ))
        self.conn.commit()
        logging.info(f"Inserted related deal for deal {item.get('dealid', '')}")

    def close_spider(self, spider):
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
        logging.info("MySQL connection closed.")
