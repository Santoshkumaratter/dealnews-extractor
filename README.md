# DealNews Scraper - Professional Web Scraping Solution

A complete, production-ready Scrapy-based web scraper for extracting deals, promotions, and reviews from dealnews.com with advanced proxy support, MySQL storage, and Docker containerization.

## 🎯 **Key Features**

- **✅ Real-time Deal Extraction** - Extracts live deals from DealNews.com
- **✅ Proxy Support** - Webshare.io integration with rotation and authentication
- **✅ MySQL Storage** - Normalized database with proper relationships
- **✅ Docker Ready** - Complete containerization for easy deployment
- **✅ Error Handling** - Comprehensive debug and early stop functionality
- **✅ Export Options** - JSON/CSV exports for data analysis
- **✅ Professional Output** - Clean, emoji-enhanced status messages

## 🚀 Quick Start

### Automated Setup (Recommended)

```bash
# 1. Clone the repository
git clone <your-repository-url>
cd dealnews

# 2. Run automated setup
python setup.py

# 3. Edit .env file with your credentials (see Configuration section)

# 4. Run the scraper
python run.py
```

### Option 1: Docker (Recommended for Production)

```bash
# 1. Clone the repository
git clone <your-repository-url>
cd dealnews-main

# 2. Create environment file
cp env.example .env
# Edit .env with your credentials (see Configuration section)

# 3. Run with Docker
docker-compose up
```

### Option 2: Manual Local Installation

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Setup MySQL (see MySQL Setup section)

# 3. Configure environment
cp env.example .env
# Edit .env with your credentials

# 4. Run the scraper
python run.py
```

## 📋 What This Scraper Does

### **Real Deal Data Extraction**
✅ **Extracts Live Data** from DealNews.com including:
- **Deal Information**: Titles, prices, descriptions, and URLs
- **Store Details**: Amazon, eBay, Walmart, Target, Best Buy, etc.
- **Categories**: Electronics, Clothing, Home & Garden, Sports, etc.
- **Promotions**: Discount codes, percentage off, special offers
- **Media**: Product images and deal thumbnails
- **Ratings**: Popularity scores and staff picks
- **Timestamps**: Publication dates and deal freshness

### **Advanced Technical Features**
✅ **Production-Ready Capabilities**:
- **Proxy Integration**: Webshare.io with authentication and rotation
- **Rate Limiting**: AutoThrottle with intelligent delay management
- **Error Recovery**: Retry mechanisms and graceful 429 handling
- **Data Normalization**: Proper MySQL schema with relationships
- **Export Flexibility**: JSON/CSV exports for analysis and backup
- **Containerization**: Docker setup for easy deployment
- **Debug & Monitoring**: Comprehensive logging and early stop functionality

## 🗄️ Database Schema

The scraper creates a normalized database with these tables:

### Main Tables
- **`deals`** - Main deal information (title, price, store, category, etc.)
- **`deal_images`** - Multiple images per deal
- **`deal_categories`** - Multiple categories per deal
- **`related_deals`** - Related deal URLs

### Sample Data Structure
```sql
-- Example deal record
dealid: "21770841"
title: "Apple iPhone 17 256GB"
price: "$0/mo. when you switch to Verizon"
store: "Verizon Home Internet"
category: "Apple"
promo: "A19 chipset - 20% faster than iPhone 16"
popularity: "Popularity: 3/5"
staffpick: "No"
```

## ⚙️ Configuration

### 1. Environment Variables (.env file)

```bash
# Webshare Proxy Credentials (Required for production)
PROXY_USER=your_webshare_username
PROXY_PASS=your_webshare_password
PROXY_HOST=p.webshare.io
PROXY_PORT=80

# MySQL Database Credentials
MYSQL_HOST=localhost
MYSQL_PORT=3307
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=dealnews

# Feature Flags
DISABLE_PROXY=false    # Set to true for local testing
DISABLE_MYSQL=false    # Set to true to export only to JSON
```

### 2. Proxy Setup (Webshare.io)

1. **Create Account**: Visit https://www.webshare.io/
2. **Purchase Plan**: Get proxy access
3. **Get Credentials**: Copy username/password from dashboard
4. **Configure**: Add credentials to .env file

### 3. MySQL Setup

#### Install MySQL
```bash
# Windows: Download from https://dev.mysql.com/downloads/mysql/
# macOS: brew install mysql
# Ubuntu: sudo apt install mysql-server
```

#### Create Database
```sql
CREATE DATABASE dealnews;
CREATE USER 'dealnews_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON dealnews.* TO 'dealnews_user'@'localhost';
FLUSH PRIVILEGES;
```

#### Initialize Schema
```bash
mysql -u dealnews_user -p dealnews < mysql_schema.sql
```

## 🐳 Docker Deployment

### Services Included
- **scraper**: Main Scrapy application
- **mysql**: MySQL 8.0 database
- **adminer**: Web-based database management

### Running with Docker
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f scraper

# Access database via Adminer
# Open http://localhost:8080
# Server: mysql, Username: dealnews_user, Database: dealnews

# Stop services
docker-compose down
```

## 📊 Data Export & Analysis

### Automatic Exports
- **JSON**: `exports/deals.json` (always created)
- **CSV**: `exports/deals.csv` (when using CSV export)

### Manual Export
```bash
# Export from Scrapy
scrapy crawl dealnews -o exports/deals.json -t json
scrapy crawl dealnews -o exports/deals.csv -t csv

# Export from MySQL
./export.sh
```

### Sample Queries
```sql
-- Get all deals from today
SELECT * FROM deals WHERE DATE(created_at) = CURDATE();

-- Get deals by category
SELECT title, price, store FROM deals WHERE category = 'electronics';

-- Get deals with promo codes
SELECT title, price, promo FROM deals WHERE promo IS NOT NULL AND promo != '';

-- Count deals by store
SELECT store, COUNT(*) as deal_count FROM deals GROUP BY store ORDER BY deal_count DESC;
```

## ⏰ Scheduling & Automation

### Daily Cron Job
```bash
# Edit crontab
crontab -e

# Add daily run at 2 AM
0 2 * * * cd /path/to/dealnews-main && python run.py
```

### Docker with Cron
```bash
# Uncomment cron section in docker-compose.yml
# Modify cron_daily_run file as needed
docker-compose up
```

## 🧪 Testing & Validation

### Test Database Connection
```bash
python -c "
import mysql.connector
conn = mysql.connector.connect(
    host='localhost', port=3307, user='root', 
    password='your_password', database='dealnews'
)
print('✅ Database connection successful!')
conn.close()
"
```

### Test Proxy (if configured)
```bash
curl -x http://username:password@p.webshare.io:80 https://httpbin.org/ip
```

### Run Unit Tests
```bash
python test_parser.py
```

## 📁 Project Structure

```
dealnews-main/
├── dealnews_scraper/          # Scrapy project
│   ├── spiders/
│   │   └── dealnews_spider.py # Main spider
│   ├── items.py               # Data definitions
│   ├── pipelines.py           # MySQL pipeline
│   ├── middlewares.py         # Proxy middleware
│   └── settings.py            # Scrapy settings
├── exports/                   # Data exports
│   ├── deals.json            # JSON data
│   └── deals.csv             # CSV data
├── mysql_schema.sql          # Database schema
├── docker-compose.yml        # Docker setup
├── Dockerfile                # Container definition
├── requirements.txt          # Dependencies
├── setup.py                  # Automated setup script
├── run.py                    # Main runner
├── run.sh                    # Shell script
├── export.sh                 # Export script
├── test_parser.py            # Unit tests
├── env.example               # Environment template
├── cron_daily_run            # Cron setup
├── .gitignore                # Git ignore file
└── README.md                 # This file
```

## 🔧 Troubleshooting

### Common Issues

1. **MySQL Connection Error**
   ```bash
   # Check MySQL is running
   brew services list | grep mysql  # macOS
   sudo systemctl status mysql      # Linux
   
   # Verify credentials in .env file
   # Ensure database exists
   mysql -u root -p -e "SHOW DATABASES;"
   ```

2. **Proxy Authentication Failed**
   ```bash
   # Test proxy manually
   curl -x http://user:pass@p.webshare.io:80 https://httpbin.org/ip
   
   # Check credentials in .env file
   # Verify proxy endpoint and port
   ```

3. **No Deals Found**
   ```bash
   # Run with debug logging
   python run.py -L DEBUG
   
   # Check if DealNews page structure changed
   # Verify CSS selectors in spider
   ```

4. **Rate Limiting (429 Errors)**
   ```bash
   # Increase delays in settings.py
   # Enable proxy to rotate IP addresses
   # Reduce concurrency settings
   ```

### Debug Mode
```bash
# Run with debug logging
python run.py -L DEBUG

# Check spider logs
tail -f scrapy.log
```

## 📈 Performance Tuning

### For Faster Scraping (use with proxy)
```python
# In settings.py
DOWNLOAD_DELAY = 1
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
```

### For Conservative Scraping
```python
# In settings.py
DOWNLOAD_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5
```

## 🎯 Key Features Summary

| Feature | Status | Description |
|---------|--------|-------------|
| **Scrapy Framework** | ✅ | Complete Scrapy project with custom spider |
| **Proxy Support** | ✅ | Webshare.io integration with rotation |
| **MySQL Storage** | ✅ | Normalized database with proper schema |
| **Data Export** | ✅ | JSON/CSV exports for analysis |
| **Docker Support** | ✅ | Complete containerization |
| **Rate Limiting** | ✅ | AutoThrottle and retry mechanisms |
| **Error Handling** | ✅ | Graceful 429 handling and fallbacks |
| **Daily Scheduling** | ✅ | Cron setup for automation |
| **Documentation** | ✅ | Comprehensive setup guide |

## 📞 Support

For issues and questions:

1. **Check the troubleshooting section above**
2. **Review logs for error messages**
3. **Verify all dependencies are installed**
4. **Ensure MySQL and proxy credentials are correct**

## 📄 License

This project is for educational and commercial use. Please respect DealNews.com's terms of service and robots.txt file.

---

## 🚀 Ready to Use!

Your DealNews scraper is now ready for production use. Simply:

1. **Configure your .env file** with credentials
2. **Run with Docker**: `docker-compose up`
3. **Or run locally**: `python run.py`
4. **Check exports/deals.json** for scraped data
5. **Access database via Adminer** at http://localhost:8080

## 🛡️ **Error Handling & Debug Features**

The scraper includes comprehensive error handling and debug functionality:

### **Early Stop Validation**
- ✅ **Environment Check**: Validates .env file and required variables
- ✅ **Dependencies Check**: Ensures all Python modules are installed
- ✅ **MySQL Connection Test**: Verifies database connectivity before starting
- ✅ **Proxy Validation**: Checks proxy credentials if enabled
- ✅ **Clear Error Messages**: Professional output with helpful instructions

### **Debug Output Example**
```
🚀 DealNews Scraper - Starting Environment Check
==================================================
🔍 Validating environment and dependencies...
✅ Environment validation passed
📦 Checking dependencies...
✅ All dependencies available
🗄️  Testing MySQL connection...
✅ MySQL connection successful
✅ All checks passed! Starting scraper...
```

**The scraper will automatically extract real deal data and store it in your MySQL database!**