# Scrapy settings for dealnews_scraper project

BOT_NAME = 'dealnews_scraper'

SPIDER_MODULES = ['dealnews_scraper.spiders']
NEWSPIDER_MODULE = 'dealnews_scraper.spiders'

ROBOTSTXT_OBEY = False
# Increase delay to reduce rate limiting and play nice with the target site
DOWNLOAD_DELAY = 3
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 5
AUTOTHROTTLE_MAX_DELAY = 30
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5
# Randomize delay between requests
RANDOMIZE_DOWNLOAD_DELAY = True

# Additional reliability controls
RETRY_ENABLED = True
RETRY_TIMES = 6
DOWNLOAD_TIMEOUT = 45
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 4

DOWNLOADER_MIDDLEWARES = {
    # Use custom user-agent rotation inside ProxyMiddleware
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'dealnews_scraper.middlewares.ProxyMiddleware': 410,
    # Ensure HttpProxyMiddleware is enabled so request.meta['proxy'] is respected
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 420,
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 550,
}

# Set a user agent to avoid being blocked
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# Handle 429 responses properly
HTTPERROR_ALLOWED_CODES = [429]
RETRY_HTTP_CODES = [500, 503, 504, 400, 403, 404, 408, 429]
RETRY_PRIORITY_ADJUST = -1

ITEM_PIPELINES = {
    'dealnews_scraper.pipelines.MySQLPipeline': 300,
}

FEED_EXPORT_ENCODING = 'utf-8'

# Export settings for JSON and CSV
FEEDS = {
    'exports/deals.json': {
        'format': 'json',
        'encoding': 'utf8',
        'store_empty': False,
        'indent': 2,
    },
    'exports/deals.csv': {
        'format': 'csv',
        'encoding': 'utf8',
        'store_empty': False,
    }
}
