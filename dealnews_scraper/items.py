import scrapy

class DealnewsItem(scrapy.Item):
    # Basic deal information
    dealid = scrapy.Field()
    recid = scrapy.Field()
    title = scrapy.Field()
    url = scrapy.Field()
    price = scrapy.Field()
    promo = scrapy.Field()
    category = scrapy.Field()
    
    # Store and vendor information
    store = scrapy.Field()
    
    # Deal details
    deal = scrapy.Field()  # e.g., "Up to 80% off"
    dealplus = scrapy.Field()  # e.g., "free shipping w/ Prime"
    
    # Deal link information
    deallink = scrapy.Field()
    dealtext = scrapy.Field()
    dealhover = scrapy.Field()
    
    # Timestamps
    published = scrapy.Field()
    created_at = scrapy.Field()
    
    # Ratings and picks
    popularity = scrapy.Field()
    staffpick = scrapy.Field()
    
    # Additional data
    detail = scrapy.Field()  # Full deal description
    raw_html = scrapy.Field()

class DealImageItem(scrapy.Item):
    dealid = scrapy.Field()
    imageurl = scrapy.Field()

class DealCategoryItem(scrapy.Item):
    dealid = scrapy.Field()
    category_name = scrapy.Field()
    category_url = scrapy.Field()
    category_title = scrapy.Field()

class RelatedDealItem(scrapy.Item):
    dealid = scrapy.Field()
    relatedurl = scrapy.Field()
