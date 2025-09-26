import scrapy
import re
import time
from dealnews_scraper.items import DealnewsItem, DealImageItem, DealCategoryItem, RelatedDealItem
from urllib.parse import urljoin, urlparse, parse_qs
from datetime import datetime

class DealnewsSpider(scrapy.Spider):
    name = "dealnews"
    allowed_domains = ["dealnews.com"]
    start_urls = [
        "https://www.dealnews.com/",
        "https://www.dealnews.com/online-stores/"
    ]

    def parse(self, response):
        self.logger.info(f"Parsing page: {response.url}")
        
        # Extract deals from current page
        deals = self.extract_deals(response)
        
        for deal in deals:
            # Create main deal item
            yield self.create_item(deal, response.text)
            
            # Create image items if images found
            if deal.get('images'):
                for image_url in deal['images']:
                    image_item = DealImageItem()
                    image_item['dealid'] = deal.get('dealid', '')
                    image_item['imageurl'] = image_url
                    yield image_item
            
            # Create category items if categories found
            if deal.get('categories'):
                for category in deal['categories']:
                    category_item = DealCategoryItem()
                    category_item['dealid'] = deal.get('dealid', '')
                    category_item['category_name'] = category.get('name', '')
                    category_item['category_url'] = category.get('url', '')
                    category_item['category_title'] = category.get('title', '')
                    yield category_item
            
            # Create related deal items if related deals found
            if deal.get('related_deals'):
                for related_url in deal['related_deals']:
                    related_item = RelatedDealItem()
                    related_item['dealid'] = deal.get('dealid', '')
                    related_item['relatedurl'] = related_url
                    yield related_item

        # Handle pagination and infinite scroll
        self.handle_pagination(response)

    def handle_pagination(self, response):
        """Handle pagination and infinite scroll for DealNews"""
        # Look for "Load More" or "Show More" buttons
        load_more_selectors = [
            'button[class*="load"]',
            'button[class*="more"]',
            'a[class*="load"]',
            'a[class*="more"]',
            '.load-more',
            '.show-more',
            '.pagination .next',
            '.pager .next'
        ]
        
        for selector in load_more_selectors:
            load_more_btn = response.css(selector)
            if load_more_btn:
                # Try to find the URL for loading more content
                href = load_more_btn.css('::attr(href)').get()
                if href:
                    yield response.follow(href, self.parse)
                    break
                
                # If it's a button, try to find data attributes
                data_url = load_more_btn.css('::attr(data-url)').get()
                if data_url:
                    yield response.follow(data_url, self.parse)
                    break
        
        # Also look for traditional pagination links
        pagination_links = response.css('.pagination a::attr(href), .pager a::attr(href)').getall()
        for link in pagination_links[:2]:  # Limit to 2 pages to avoid infinite loops
            if link and 'page=' in link:
                yield response.follow(link, self.parse)

    def extract_deals(self, response):
        deals = []
        
        # Use the correct DealNews selector based on actual HTML structure
        deal_elements = response.css('.content-card')
        
        if deal_elements:
            self.logger.info(f"Found {len(deal_elements)} content cards")
            
            # Process each element
            for element in deal_elements:
                deal = self.extract_deal_from_element(element, response)
                if deal and self.is_valid_deal(deal):
                    deals.append(deal)
        
        self.logger.info(f"Total deals extracted: {len(deals)}")
        return deals

    def is_valid_deal(self, deal):
        """Validate if a deal has minimum required information"""
        return (
            deal.get('title') and len(deal['title'].strip()) > 5 and
            (deal.get('url') or deal.get('deallink')) and
            (deal.get('price') or deal.get('deal') or deal.get('store'))
        )

    def extract_deal_from_element(self, element, response):
        deal = {}
        
        # Extract deal ID from data attributes (based on HTML analysis)
        deal['dealid'] = element.css('::attr(data-content-id)').get() or ''
        
        # Extract URL from data attributes or links
        url = element.css('::attr(data-offer-url)').get()
        if not url:
            # Fallback to link href
            url = element.css('a::attr(href)').get()
        
        if url and not url.startswith('#') and len(url) > 10:
            deal['url'] = urljoin(response.url, url)
            # Extract recid from URL parameters if present
            parsed_url = urlparse(deal['url'])
            query_params = parse_qs(parsed_url.query)
            deal['recid'] = query_params.get('recid', [''])[0]
        else:
            deal['url'] = ''
            deal['recid'] = ''
        
        # Extract title using correct DealNews selector
        title = element.css('.title::text').get()
        if title and len(title.strip()) > 5:
            deal['title'] = title.strip()
        else:
            # Fallback to title attribute
            title = element.css('.title::attr(title)').get()
            if title and len(title.strip()) > 5:
                deal['title'] = title.strip()
            else:
                deal['title'] = ''
        
        # Extract price - look for $ signs in text content
        all_text = element.css('::text').getall()
        for text in all_text:
            text = text.strip()
            if '$' in text and any(char.isdigit() for char in text) and len(text) < 20:
                deal['price'] = text
                break
        else:
            deal['price'] = ''
        
        # Extract promo/coupon code - look for percentage or discount text
        all_text = element.css('::text').getall()
        for text in all_text:
            text = text.strip()
            if ('%' in text or 'off' in text.lower() or 'save' in text.lower()) and len(text) < 50:
                deal['promo'] = text
                break
        else:
            deal['promo'] = ''
        
        # Extract store from published date text (e.g., "Amazon · 16 hrs ago")
        all_text = element.css('::text').getall()
        store = ''
        for text in all_text:
            text = text.strip()
            if '·' in text and ('hrs ago' in text or 'days ago' in text or 'mins ago' in text):
                # Extract store name before the "·" symbol
                store = text.split('·')[0].strip()
                break
        
        # Fallback to data-store attribute if no store found in text
        if not store:
            store_id = element.css('::attr(data-store)').get()
            if store_id:
                # Map store ID to store name
                store_mapping = {
                    '313': 'Amazon',
                    '1': 'Walmart', 
                    '2': 'Target',
                    '3': 'Best Buy',
                    '4': 'eBay',
                    '5': 'Home Depot',
                    '6': 'Macy\'s',
                    '7': 'Nike',
                    '8': 'adidas',
                    '9': 'REI',
                    '10': 'Dick\'s Sporting Goods'
                }
                store = store_mapping.get(store_id, f'Store_{store_id}')
        
        deal['store'] = store.strip() if store else ''
        
        # Extract deal description from snippet or use title as fallback
        deal_text = element.css('.snippet::text').get()
        if deal_text and len(deal_text.strip()) > 10:
            deal['deal'] = deal_text.strip()
        else:
            # Fallback to title if no snippet available
            deal['deal'] = deal.get('title', '')
        
        # Extract deal plus (additional info) - use callout text
        dealplus = element.css('.callout::text').get()
        deal['dealplus'] = dealplus.strip() if dealplus else ''
        
        # Extract deal link - use the main link
        deallink = element.css('a::attr(href)').get()
        if deallink and not deallink.startswith('#') and len(deallink) > 10:
            deal['deallink'] = urljoin(response.url, deallink)
        else:
            deal['deallink'] = deal.get('url', '')
        
        # Extract deal text (button text) - use CTA button text
        dealtext = element.css('.btn-cta::text').get()
        deal['dealtext'] = dealtext.strip() if dealtext else ''
        
        # Extract deal hover text - use aria-label
        dealhover = element.css('a::attr(aria-label)').get()
        deal['dealhover'] = dealhover.strip() if dealhover else ''
        
        # Extract published date - look for time patterns in text
        all_text = element.css('::text').getall()
        for text in all_text:
            text = text.strip()
            if 'hrs ago' in text or 'days ago' in text or 'mins ago' in text:
                deal['published'] = text
                break
        else:
            deal['published'] = ''
        
        # Extract popularity - look for "Popularity: X/5" pattern
        for text in all_text:
            text = text.strip()
            if 'Popularity:' in text:
                deal['popularity'] = text
                break
        else:
            deal['popularity'] = ''
        
        # Extract staff pick flag - check for staff pick badge
        staffpick = element.css('.badges .icon[href="#ic-staff-pick"]').get()
        deal['staffpick'] = 'Yes' if staffpick else 'No'
        
        # Extract detail/description - use snippet as detail
        detail = element.css('.snippet::text').get()
        deal['detail'] = detail.strip() if detail else ''
        
        # Extract images
        img_url = element.css('img::attr(src)').get()
        if img_url and not img_url.startswith('data:') and len(img_url) > 10:
            deal['images'] = [urljoin(response.url, img_url)]
        else:
            deal['images'] = []
        
        # Extract categories from chips
        categories = []
        chip_links = element.css('.chip::attr(href)').getall()
        chip_titles = element.css('.chip::attr(title)').getall()
        for i, link in enumerate(chip_links):
            if link and i < len(chip_titles):
                categories.append({
                    'name': chip_titles[i].strip() if i < len(chip_titles) else '',
                    'url': urljoin(response.url, link),
                    'title': chip_titles[i].strip() if i < len(chip_titles) else ''
                })
        deal['categories'] = categories
        
        # Extract related deals - not available in current structure
        deal['related_deals'] = []
        
        # Set defaults for missing fields
        deal.setdefault('dealid', '')
        deal.setdefault('recid', '')
        deal.setdefault('url', '')
        deal.setdefault('title', '')
        deal.setdefault('price', '')
        deal.setdefault('promo', '')
        # Extract category from breadcrumb - get the last breadcrumb item (actual category)
        breadcrumb_links = element.css('.breadcrumb a::text').getall()
        category = ''
        if breadcrumb_links:
            # Get the last breadcrumb item which is usually the category
            category = breadcrumb_links[-1].strip()
        
        # Fallback to data-category attribute if no category found in breadcrumb
        if not category:
            category_id = element.css('::attr(data-category)').get()
            if category_id:
                # Map category ID to category name
                category_mapping = {
                    '196': 'Home & Garden',
                    '280': 'Clothing & Accessories',
                    '202': 'Clothing & Accessories', 
                    '1': 'Electronics',
                    '2': 'Clothing',
                    '3': 'Computers',
                    '4': 'Health & Beauty',
                    '5': 'Sports & Outdoors'
                }
                category = category_mapping.get(category_id, f'Category_{category_id}')
        
        deal.setdefault('category', category.strip() if category else 'general')
        deal.setdefault('store', '')
        deal.setdefault('deal', '')
        deal.setdefault('dealplus', '')
        deal.setdefault('deallink', '')
        deal.setdefault('dealtext', '')
        deal.setdefault('dealhover', '')
        deal.setdefault('published', '')
        deal.setdefault('popularity', '')
        deal.setdefault('staffpick', '')
        deal.setdefault('detail', '')
        
        return deal

    def extract_category_from_url(self, url):
        """Extract category from URL - updated for current DealNews structure"""
        if '/online-stores/' in url:
            return 'stores'
        elif '/c/electronics/' in url or '/electronics/' in url:
            return 'electronics'
        elif '/c/clothing/' in url or '/clothing/' in url or '/fashion/' in url:
            return 'clothing'
        elif '/c/home-garden/' in url or '/home/' in url or '/garden/' in url:
            return 'home'
        elif '/c/computers/' in url or '/computers/' in url or '/tech/' in url:
            return 'computers'
        elif '/c/health-beauty/' in url or '/health/' in url or '/beauty/' in url:
            return 'health'
        elif '/c/sports-outdoors/' in url or '/sports/' in url or '/outdoors/' in url:
            return 'sports'
        elif '/c/automotive/' in url or '/auto/' in url or '/car/' in url:
            return 'automotive'
        elif '/c/books-movies-music/' in url or '/books/' in url or '/movies/' in url:
            return 'entertainment'
        elif '/categories/' in url:
            return 'categories'
        else:
            return 'general'

    def create_item(self, deal, raw_html):
        """Create a DealnewsItem from extracted deal data"""
        item = DealnewsItem()
        
        # Map all fields from deal to item
        item['dealid'] = deal.get('dealid', '')
        item['recid'] = deal.get('recid', '')
        item['url'] = deal.get('url', '')
        item['title'] = deal.get('title', '')
        item['price'] = deal.get('price', '')
        item['promo'] = deal.get('promo', '')
        item['category'] = deal.get('category', 'general')
        item['store'] = deal.get('store', '')
        item['deal'] = deal.get('deal', '')
        item['dealplus'] = deal.get('dealplus', '')
        item['deallink'] = deal.get('deallink', '')
        item['dealtext'] = deal.get('dealtext', '')
        item['dealhover'] = deal.get('dealhover', '')
        item['published'] = deal.get('published', '')
        item['popularity'] = deal.get('popularity', '')
        item['staffpick'] = deal.get('staffpick', '')
        item['detail'] = deal.get('detail', '')
        item['raw_html'] = raw_html[:10000] if raw_html else ''  # Limit HTML size
        
        return item
