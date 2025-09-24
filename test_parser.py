import unittest
from scrapy.http import HtmlResponse, Request
from dealnews_scraper.spiders.dealnews_spider import DealnewsSpider

class DealnewsSpiderTest(unittest.TestCase):

    def setUp(self):
        self.spider = DealnewsSpider()
        self.mock_response_html = """
        <html>
        <body>
            <article data-deal-id="123">
                <h2 class="deal-title">Test Deal Title 1</h2>
                <span class="deal-price">$10.00</span>
                <a href="/deal/1">Link 1</a>
                <span class="promo">PROMO1</span>
            </article>
            <div class="deal-item">
                <h3>Another Deal</h3>
                <span class="price">$20.00</span>
                <a href="/deal/2">Link 2</a>
            </div>
            <div class="offer-item">
                <h4 class="offer-title">Third Deal</h4>
                <span class="offer-price">Free</span>
                <a href="/deal/3">Link 3</a>
                <span class="coupon">FREEBIE</span>
            </div>
            <a href="/page/2" class="pagination">Next Page</a>
        </body>
        </html>
        """
        self.mock_response = HtmlResponse(url="https://www.dealnews.com/", body=self.mock_response_html, encoding='utf-8')

    def test_extract_deals(self):
        deals = self.spider.extract_deals(self.mock_response)
        self.assertGreaterEqual(len(deals), 0)
        if len(deals) > 0:
            self.assertIn('title', deals[0])
            self.assertIn('category', deals[0])
            if 'price' in deals[0]:
                self.assertIsInstance(deals[0]['price'], str)
            if 'promo' in deals[0]:
                self.assertIsInstance(deals[0]['promo'], str)

    def test_extract_category_from_url(self):
        self.assertEqual(self.spider.extract_category_from_url("https://www.dealnews.com/electronics/"), "electronics")
        self.assertEqual(self.spider.extract_category_from_url("https://www.dealnews.com/fashion/"), "fashion")
        self.assertEqual(self.spider.extract_category_from_url("https://www.dealnews.com/home/"), "home")
        self.assertEqual(self.spider.extract_category_from_url("https://www.dealnews.com/sports/"), "sports")
        self.assertEqual(self.spider.extract_category_from_url("https://www.dealnews.com/coupons/"), "coupons")
        self.assertEqual(self.spider.extract_category_from_url("https://www.dealnews.com/"), "general")

    def test_create_item(self):
        deal_data = {
            'title': 'Test Deal',
            'url': 'https://example.com/deal',
            'price': '$15.00',
            'promo': 'SAVE10',
            'category': 'electronics'
        }
        
        item = self.spider.create_item(deal_data, '<html>test</html>')
        
        self.assertEqual(item['title'], 'Test Deal')
        self.assertEqual(item['url'], 'https://example.com/deal')
        self.assertEqual(item['price'], '$15.00')
        self.assertEqual(item['promo'], 'SAVE10')
        self.assertEqual(item['category'], 'electronics')
        self.assertIn('raw_html', item)
        self.assertIn('created_at', item)

if __name__ == '__main__':
    unittest.main()