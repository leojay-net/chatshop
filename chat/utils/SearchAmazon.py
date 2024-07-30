from selectorlib import Extractor
import requests
from typing import Dict, List, Any

YAML_STRING = """
products:
    css: 'div[data-component-type="s-search-result"]'
    xpath: null
    multiple: true
    type: Text
    children:
        title:
            css: 'h2 a.a-link-normal.a-text-normal'
            xpath: null
            type: Text
        url:
            css: 'h2 a.a-link-normal.a-text-normal'
            xpath: null
            type: Link
        image:
            css: 'img.s-image'
            xpath: null
            type: Attribute
            attribute: src
        rating:
            css: 'div.a-row.a-size-small span:nth-of-type(1)'
            xpath: null
            type: Attribute
            attribute: aria-label
        number_of_ratings:
            css: 'div.a-row.a-size-small span:nth-of-type(2)'
            xpath: null
            type: Attribute
            attribute: aria-label
        price:
            css: 'span.a-price:nth-of-type(1) span.a-offscreen'
            xpath: null
            type: Text
        original_price:
            css: 'span.a-price.a-text-price span.a-offscreen'
            xpath: null
            type: Text
        discount:
            css: 'span.a-price ~ span.a-letter-space + span'
            xpath: null
            type: Text
        is_sponsored:
            css: 'span.s-label-popover-default'
            xpath: null
            type: Text
        delivery_info:
            css: 'div.a-row.a-size-base.a-color-secondary.s-align-children-center > span.a-color-base'
            xpath: null
            type: Text
"""

class AmazonSearchExtractor:
    def __init__(self):
        self._extractor = Extractor.from_yaml_string(YAML_STRING)

    def _scrape(self, url: str, headers: Dict[str, str] = None) -> Dict[str, Any]:
        if not headers:
            headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Sec-Fetch-Site": "none",
                "Host": "www.amazon.com",
                "Accept-Language": "en-IN,en-GB;q=0.9,en;q=0.8",
                "Sec-Fetch-Mode": "navigate",
                "Accept-Encoding": "gzip, deflate, br",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Priority": "u=0, i",
            }

        response = requests.get(url, headers=headers)

        if response.status_code > 500:
            raise Exception(f"Page {url} was blocked by Amazon. Please try using better proxies.")
        
        return self._extractor.extract(response.text)

    def _process_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        processed = {}
        
        processed['title'] = product.get('title', '').strip()
        processed['url'] = f"https://www.amazon.in{product.get('url', '')}"
        processed['image'] = product.get('image', '')
        
        rating = product.get('rating', '')
        processed['rating'] = float(rating.replace('out of 5 stars', '').strip()) if rating else None
        
        num_ratings = product.get('number_of_ratings', '')
        processed['number_of_ratings'] = int(num_ratings.replace(',', '').strip().split(' ')[0]) if num_ratings else None
        
        processed['price'] = product.get('price', '').strip().replace(" ", "")
        processed['original_price'] = product.get('original_price', '').strip()
        #processed['discount'] = product.get('discount', '').strip()
        processed['is_sponsored'] = product.get('is_sponsored') == 'Sponsored'
        processed['source'] = 'Amazon'
        
        return processed

    def search(self, query: str, page: int = 1, headers: Dict[str, str] = None) -> Dict[str, List[Dict[str, Any]]]:
        url = f"https://www.amazon.com/s?k={query}&page={page}&currency=NGN"
        raw_data = self._scrape(url, headers)
        
        processed_products = [self._process_product(product) for product in raw_data.get('products', [])]
        
        return {
            "query": query,
            "page": page,
            "products": processed_products
        }

# # Usage example:
# if __name__ == "__main__":
#     extractor = AmazonSearchExtractor()
#     results = extractor.search("laptop", page=1)
    
#     print(f"Found {len(results['products'])} products:")
#     for product in results['products']:
#         print(f"Title: {product['title']}")
#         print(f"Price: {product['price']}")
#         print(f"Rating: {product['rating']}")
#         print(f"Number of ratings: {product['number_of_ratings']}")
#         print(f"Image URL: {product['image']}")
#         print("-" * 50)