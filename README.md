# DealNews Scraper

A robust Scrapy-based web scraper for extracting deals, promotions, and reviews from dealnews.com with proxy support, MySQL storage, and Docker containerization.

## Features

- **Comprehensive Scraping**: Extracts deals from multiple categories on DealNews.com
- **Proxy Support**: Webshare.io proxy integration with authentication, rotation, and error handling
- **MySQL Storage**: Normalized data storage with proper schema and duplicate prevention
- **Reliability Features**: AutoThrottle, retry mechanisms, and graceful 429 handling
- **Docker Support**: Full containerization with docker-compose for Scrapy, MySQL, and Adminer
- **Export Options**: CSV/JSON export for debugging and analysis (data is always saved to JSON files in exports/)
- **Cron Scheduling**: Daily automated runs with configurable rate limiting
- **Fallback Mechanism**: Automatic JSON export when MySQL is unavailable

## Requirements

- Python 3.9+
- MySQL 8.0+
- Docker & Docker Compose (optional)
- Webshare.io proxy account (optional)

## Quick Start

**Important Note**: The scraper automatically saves all scraped data to JSON files in the `exports/` directory. You can always view the latest data in `exports/deals.json` even if MySQL is not available.

### Option 1: Docker (Recommended)

1. **Clone the repository**
```bash
git clone <repository-url>
cd  dealnews

```

2. **Create environment file**
```bash
cp env.example .env
# Edit .env with your credentials
```

3. **Run with Docker**
```bash
docker-compose up
```

### Option 2: Local Installation

1. **Install Python dependencies**
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. **Setup MySQL** (see MySQL Setup section)

3. **Configure environment**
```bash
cp env.example .env
# Edit .env with your credentials
```

4. **Run the scraper**
```bash
python run.py
```

## MySQL Setup

### Install MySQL

#### macOS (using Homebrew)
```bash
brew install mysql
brew services start mysql
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install mysql-server
sudo systemctl start mysql
sudo systemctl enable mysql
```

#### Windows
Download MySQL installer from https://dev.mysql.com/downloads/mysql/

### Create Database and User

1. **Login to MySQL**
```bash
mysql -u root -p
```

2. **Create database and user**
```sql
CREATE DATABASE dealnews;
CREATE USER 'dealnews_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON dealnews.* TO 'dealnews_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

3. **Initialize database schema**
```bash
mysql -u dealnews_user -p dealnews < mysql_schema.sql
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Webshare Proxy Credentials (Optional - for production use)
PROXY_USER=your_webshare_username
PROXY_PASS=your_webshare_password
PROXY_HOST=p.webshare.io
PROXY_PORT=80
# Optional: provide a list of proxies (one per line or comma-separated)
# PROXY_LIST=http://host1:port,http://host2:port

# Optional: Set to 'false' to disable proxy for local testing
USE_PROXY=true

# MySQL Database Credentials
MYSQL_HOST=localhost
MYSQL_PORT=3307
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DATABASE=dealnews
MYSQL_ROOT_PASSWORD=root

# Optional: Save HTML snapshots for auditing
SAVE_HTML_SNAPSHOTS=false
SNAPSHOTS_DIR=exports/html_snapshots

# Feature flags
DISABLE_PROXY=false  # Set to true to disable proxy for local testing
DISABLE_MYSQL=false  # Set to true to disable MySQL pipeline (will only export to JSON)
```

### Proxy Setup (Webshare.io)

1. **Create Webshare Account**
   - Visit https://www.webshare.io/
   - Sign up for an account
   - Purchase a proxy plan

2. **Get Credentials**
   - Login to your Webshare dashboard
   - Go to "Proxy List" section
   - Copy your username and password
   - Note the proxy endpoint (usually p.webshare.io:80)

3. **Configure in .env**
```bash
PROXY_USER=your_username
PROXY_PASS=your_password
```

## Database Schema

The scraper creates and uses the following table structure:

```sql
-- Main deals table
CREATE TABLE deals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dealid VARCHAR(100),
    recid VARCHAR(100),
    url VARCHAR(500) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    price VARCHAR(100),
    promo VARCHAR(255),
    category VARCHAR(100) DEFAULT 'general',
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
);

-- Images table for multiple images per deal
CREATE TABLE deal_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dealid VARCHAR(100),
    imageurl VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_dealid (dealid)
);

-- Categories table for multiple categories per deal
CREATE TABLE deal_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dealid VARCHAR(100),
    category_name VARCHAR(100),
    category_url VARCHAR(500),
    category_title VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_dealid (dealid)
);

-- Related deals table
CREATE TABLE related_deals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dealid VARCHAR(100),
    relatedurl VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_dealid (dealid)
);
```

### Sample Queries

```sql
-- Get all deals
SELECT * FROM deals ORDER BY created_at DESC;

-- Get deals by category
SELECT * FROM deals WHERE category = 'electronics';

-- Get deals with prices
SELECT title, price, url FROM deals WHERE price != '';

-- Get recent deals (last 24 hours)
SELECT * FROM deals WHERE created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY);

-- Count deals by category
SELECT category, COUNT(*) as count FROM deals GROUP BY category;
```

## Usage

### Running the Scraper

#### Single Run
```bash
python run.py
```

#### With Command Line Options
```bash
# Run without MySQL (export to JSON only)
python run.py --no-mysql

# Run without proxy
python run.py --no-proxy

# Limit number of items to scrape
python run.py --items 10
```

#### Using Shell Scripts
```bash
# Run scraper
./run.sh

# Export data to CSV/JSON
./export.sh
```

#### Using Docker
```bash
# Run once
docker-compose run scraper

# Run with database
docker-compose up
```

### Exporting Data

```bash
# Export to JSON directly from Scrapy
scrapy crawl dealnews -o exports/deals.json -t json

# Export to CSV directly from Scrapy
scrapy crawl dealnews -o exports/deals.csv -t csv

# Use export script (exports from MySQL)
./export.sh
```

**Note**: The scraper automatically saves data to JSON files in the `exports/` directory even when MySQL is unavailable. You can always check the latest scraped data in `exports/deals.json` without needing to query the database.

## Docker Setup

### Services

The `docker-compose.yml` includes:

- **scraper**: The main Scrapy application
- **mysql**: MySQL 8.0 database
- **adminer**: Web-based database management

### Running with Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f scraper

# Stop services
docker-compose down
```

### Database Access

- **Adminer**: http://localhost:8080
  - Server: mysql
  - Username: dealnews_user
  - Password: (from .env file)
  - Database: dealnews

## Scheduling

### Daily Cron Job

1. **Create cron file**
```bash
# Edit crontab
crontab -e

# Add daily run at 2 AM
0 2 * * * cd /path/to/dealnews-main && python run.py
```

2. **Using Docker with Cron**
```bash
# Uncomment cron section in docker-compose.yml
# Modify cron_daily_run file as needed
docker-compose up
```

3. **Cron with Environment Variables**
```bash
# Create a wrapper script for cron
cat > run_cron.sh << 'EOF'
#!/bin/bash
cd /path/to/dealnews-main
source .env
python run.py
EOF

chmod +x run_cron.sh

# Add to crontab
0 2 * * * /path/to/dealnews-main/run_cron.sh
```

## Testing

### Run Unit Tests
```bash
python test_parser.py
```

### Test Database Connection
```bash
python -c "
import mysql.connector
conn = mysql.connector.connect(
    host='localhost',
    port=3307,
    user='root',
    password='root',
    database='dealnews'
)
print('Database connection successful!')
conn.close()
"
```

### Test Proxy (if configured)
```bash
curl -x http://username:password@p.webshare.io:80 https://httpbin.org/ip
```

## Project Structure

```
dealnews-main/
├── dealnews_scraper/
│   ├── spiders/
│   │   └── dealnews_spider.py
│   ├── items.py
│   ├── pipelines.py
│   ├── middlewares.py
│   └── settings.py
├── exports/
│   ├── deals.json
│   └── deals.csv
├── mysql_schema.sql
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── run.py
├── run.sh
├── export.sh
├── test_parser.py
├── env.example
├── cron_daily_run
└── README.md
```

## Troubleshooting

### Common Issues

1. **MySQL Connection Error**
   - Verify MySQL is running: `brew services list | grep mysql`
   - Check credentials in `.env` file
   - Ensure database exists: `mysql -u root -p -e "SHOW DATABASES;"`

2. **Proxy Authentication Failed**
   - Verify Webshare credentials
   - Check proxy endpoint and port
   - Test with curl: `curl -x http://user:pass@p.webshare.io:80 https://httpbin.org/ip`

3. **No Deals Found**
   - Check if DealNews page structure changed
   - Run with debug logging: `python run_spider.py -L DEBUG`
   - Verify CSS selectors in spider

4. **Rate Limiting (429 Errors)**
   - Increase `DOWNLOAD_DELAY` in settings.py
   - Enable proxy to rotate IP addresses
   - Reduce `AUTOTHROTTLE_TARGET_CONCURRENCY`

### Debug Mode

```bash
# Run with debug logging
python run_spider.py -L DEBUG

# Check spider logs
tail -f scrapy.log
```

## Performance Tuning

### Settings Optimization

```python
# For faster scraping (use with proxy)
DOWNLOAD_DELAY = 1
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

# For more conservative scraping
DOWNLOAD_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5
```

### Database Optimization

```sql
-- Add indexes for better performance
CREATE INDEX idx_category ON deals(category);
CREATE INDEX idx_created_at ON deals(created_at);
CREATE INDEX idx_price ON deals(price(10));
```

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review the logs for error messages
3. Verify all dependencies are installed
4. Ensure MySQL and proxy credentials are correct

## License

This project is for educational and commercial use. Please respect DealNews.com's terms of service and robots.txt file.