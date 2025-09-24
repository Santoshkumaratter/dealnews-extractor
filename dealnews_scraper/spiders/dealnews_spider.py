import scrapy
import re
from dealnews_scraper.items import DealnewsItem, DealImageItem, DealCategoryItem, RelatedDealItem
from urllib.parse import urljoin, urlparse, parse_qs
from datetime import datetime

class DealnewsSpider(scrapy.Spider):
    name = "dealnews"
    allowed_domains = ["dealnews.com"]
    start_urls = [
        "https://www.dealnews.com/",
        "https://www.dealnews.com/categories/",
        "https://www.dealnews.com/online-stores/"
    ]

    def parse(self, response):
        self.logger.info(f"Parsing page: {response.url}")
        
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

        pagination_links = response.css('.pagination a::attr(href), .pager a::attr(href), .next::attr(href)').getall()
        for link in pagination_links[:3]:
            yield response.follow(link, self.parse)

    def extract_deals(self, response):
        deals = []
        
        # Modern DealNews selectors - updated for current website structure
        deal_selectors = [
            # Primary selectors for deals
            '.deal-card',
            '.deal-tile',
            '.card-deal', 
            '.deal',
            # Secondary selectors
            '.offer-item',
            'article[data-deal-id]',
            'article[class*="deal"]',
            # Fallback selectors
            'article',
            '[class*="deal"]',
            '[class*="offer"]',
            '[class*="coupon"]',
            # Last resort
            '.item',
            '.product-card'
        ]
        
        # Try each selector until we find deals
        for selector in deal_selectors:
            deal_elements = response.css(selector)
            if deal_elements:
                self.logger.info(f"Found {len(deal_elements)} elements with selector: {selector}")
                
                # Process each element (limit to 50 per page for performance)
                for element in deal_elements[:50]:
                    deal = self.extract_deal_from_element(element, response)
                    if deal:
                        deals.append(deal)
                
                # If we found deals with this selector, stop trying others
                if deals:
                    break
        
        # If we still don't have deals, try a more aggressive approach
        if not deals:
            self.logger.info("No deals found with standard selectors, trying alternative approach")
            # Look for any clickable elements with prices
            price_elements = response.css('a:contains("$")') + response.css('[class*="price"]').css('a')
            for element in price_elements[:50]:
                deal = self.extract_deal_from_element(element, response)
                if deal:
                    deals.append(deal)
        
        self.logger.info(f"Total deals extracted: {len(deals)}")
        return deals

    def extract_deal_from_element(self, element, response):
        deal = {}
        
        # Extract deal ID and rec ID from URL
        url_selectors = [
            'a::attr(href)', '.deal-link::attr(href)', '.offer-link::attr(href)',
            '[href]::attr(href)'
        ]
        
        for selector in url_selectors:
            url = element.css(selector).get()
            if url and not url.startswith('#') and len(url) > 10:
                deal['url'] = urljoin(response.url, url)
                # Extract dealid and recid from URL parameters
                parsed_url = urlparse(deal['url'])
                query_params = parse_qs(parsed_url.query)
                deal['dealid'] = query_params.get('dealid', [''])[0]
                deal['recid'] = query_params.get('recid', [''])[0]
                break
        
        # Extract title
        title_selectors = [
            'h1::text', 'h2::text', 'h3::text', 'h4::text',
            '.title::text', '.deal-title::text', '.offer-title::text',
            'a[title]::attr(title)', 'a::text',
            '[class*="title"]::text'
        ]
        
        for selector in title_selectors:
            title = element.css(selector).get()
            if title and len(title.strip()) > 5:
                deal['title'] = title.strip()
                break
        
        # Extract price
        price_selectors = [
            '.price::text', '.deal-price::text', '.offer-price::text',
            '[class*="price"]::text', '.amount::text',
            '[class*="cost"]::text', '[class*="amount"]::text'
        ]
        
        for selector in price_selectors:
            price = element.css(selector).get()
            if price and ('$' in price or 'free' in price.lower() or '%' in price):
                deal['price'] = price.strip()
                break
        
        # Extract promo codes
        promo_selectors = [
            '.promo::text', '.coupon::text', '.code::text',
            '[class*="promo"]::text', '[class*="coupon"]::text',
            '[class*="code"]::text'
        ]
        
        for selector in promo_selectors:
            promo = element.css(selector).get()
            if promo and len(promo.strip()) > 2:
                deal['promo'] = promo.strip()
                break
        
        # Extract store information
        store_selectors = [
            '.store::text', '.vendor::text', '.retailer::text',
            '[class*="store"]::text', '[class*="vendor"]::text',
            '.brand::text', '[class*="brand"]::text'
        ]
        
        for selector in store_selectors:
            store = element.css(selector).get()
            if store and len(store.strip()) > 2:
                deal['store'] = store.strip()
                break
        
        # If no store found, try to extract from title or URL
        if not deal.get('store'):
            if 'amazon' in deal.get('title', '').lower():
                deal['store'] = 'Amazon'
            elif 'amazon' in deal.get('url', '').lower():
                deal['store'] = 'Amazon'
        
        # Extract deal information (discounts, offers)
        deal_selectors = [
            '.deal::text', '.discount::text', '.savings::text',
            '[class*="deal"]::text', '[class*="discount"]::text',
            '[class*="offer"]::text', '[class*="savings"]::text'
        ]
        
        for selector in deal_selectors:
            deal_text = element.css(selector).get()
            if deal_text and ('%' in deal_text or 'off' in deal_text.lower()):
                deal['deal'] = deal_text.strip()
                break
        
        # Extract deal plus (additional benefits like free shipping)
        dealplus_selectors = [
            '.dealplus::text', '.bonus::text', '.extra::text',
            '[class*="shipping"]::text', '[class*="bonus"]::text'
        ]
        
        for selector in dealplus_selectors:
            dealplus = element.css(selector).get()
            if dealplus and ('free' in dealplus.lower() or 'shipping' in dealplus.lower()):
                deal['dealplus'] = dealplus.strip()
                break
        
        # Extract deal link information
        deal_link_element = element.css('a[href*="shop"], a[href*="buy"], a[href*="deal"]').get()
        if deal_link_element:
            deal_link_selector = element.css('a[href*="shop"], a[href*="buy"], a[href*="deal"]')
            deal['deallink'] = deal_link_selector.css('::attr(href)').get()
            deal['dealtext'] = deal_link_selector.css('::text').get()
            deal['dealhover'] = deal_link_selector.css('::attr(title)').get()
        
        # Extract published timestamp
        published_selectors = [
            '.published::text', '.date::text', '.timestamp::text',
            '[class*="published"]::text', '[class*="date"]::text',
            '[class*="time"]::text'
        ]
        
        for selector in published_selectors:
            published = element.css(selector).get()
            if published and ('hr' in published or 'day' in published or 'ago' in published):
                deal['published'] = published.strip()
                break
        
        # Extract popularity rating
        popularity_selectors = [
            '.popularity::text', '.rating::text', '.score::text',
            '[class*="popularity"]::text', '[class*="rating"]::text'
        ]
        
        for selector in popularity_selectors:
            popularity = element.css(selector).get()
            if popularity and ('/' in popularity or 'star' in popularity.lower()):
                deal['popularity'] = popularity.strip()
                break
        
        # Extract staff pick information
        staffpick_selectors = [
            '.staffpick::text', '.featured::text', '.recommended::text',
            '[class*="staff"]::text', '[class*="pick"]::text'
        ]
        
        for selector in staffpick_selectors:
            staffpick = element.css(selector).get()
            if staffpick and len(staffpick.strip()) > 2:
                deal['staffpick'] = staffpick.strip()
                break
        
        # Extract full detail/description
        detail_selectors = [
            '.detail::text', '.description::text', '.content::text',
            '[class*="detail"]::text', '[class*="description"]::text'
        ]
        
        for selector in detail_selectors:
            detail = element.css(selector).get()
            if detail and len(detail.strip()) > 20:
                deal['detail'] = detail.strip()
                break
        
        # Extract images
        deal['images'] = []
        image_selectors = [
            'img::attr(src)', 'img::attr(data-src)', '[class*="image"] img::attr(src)'
        ]
        
        for selector in image_selectors:
            images = element.css(selector).getall()
            for img in images:
                if img and not img.startswith('data:'):
                    deal['images'].append(urljoin(response.url, img))
        
        # Extract categories
        deal['categories'] = []
        category_elements = element.css('[class*="category"], [class*="tag"], .breadcrumb a')
        for cat_elem in category_elements:
            category = {}
            category['name'] = cat_elem.css('::text').get()
            category['url'] = cat_elem.css('::attr(href)').get()
            category['title'] = cat_elem.css('::attr(title)').get()
            if category['name']:
                deal['categories'].append(category)
        
        # Extract related deals
        deal['related_deals'] = []
        related_selectors = [
            '.related a::attr(href)', '.similar a::attr(href)',
            '[class*="related"] a::attr(href)'
        ]
        
        for selector in related_selectors:
            related_urls = element.css(selector).getall()
            for url in related_urls:
                if url and not url.startswith('#'):
                    deal['related_deals'].append(urljoin(response.url, url))
        
        deal['category'] = self.extract_category_from_url(response.url)
        
        if deal.get('title') and len(deal['title']) > 10:
            return deal
        elif deal.get('price') and deal.get('url'):
            return deal
        
        return None

    def create_item(self, deal_data, html_content):
        item = DealnewsItem()
        
        # Basic deal information
        item['dealid'] = deal_data.get('dealid', '')
        item['recid'] = deal_data.get('recid', '')
        item['title'] = deal_data.get('title', '')
        item['url'] = deal_data.get('url', '')
        item['price'] = deal_data.get('price', '')
        item['promo'] = deal_data.get('promo', '')
        item['category'] = deal_data.get('category', 'general')
        
        # Store and vendor information
        item['store'] = deal_data.get('store', '')
        
        # Deal details
        item['deal'] = deal_data.get('deal', '')
        item['dealplus'] = deal_data.get('dealplus', '')
        
        # Deal link information
        item['deallink'] = deal_data.get('deallink', '')
        item['dealtext'] = deal_data.get('dealtext', '')
        item['dealhover'] = deal_data.get('dealhover', '')
        
        # Timestamps
        item['published'] = deal_data.get('published', '')
        item['created_at'] = datetime.now().isoformat()
        
        # Ratings and picks
        item['popularity'] = deal_data.get('popularity', '')
        item['staffpick'] = deal_data.get('staffpick', '')
        
        # Additional data
        item['detail'] = deal_data.get('detail', '')
        item['raw_html'] = html_content[:5000] if html_content else ''
        
        return item

    def extract_category_from_url(self, url):
        if '/online-stores/' in url:
            return 'stores'
        elif '/c/electronics/' in url:
            return 'electronics'
        elif '/c/clothing/' in url:
            return 'clothing'
        elif '/c/home-garden/' in url:
            return 'home'
        elif '/c/computers/' in url:
            return 'computers'
        elif '/categories/' in url:
            return 'categories'
        else:
            return 'general'
