from selectorlib import Extractor
import requests
from typing import Dict, List, Any

YAML_STRING = """
products:
    css: 'article.prd'
    xpath: null
    multiple: true
    type: Text
    children:
        title:
            css: 'h3.name'
            xpath: null
            type: Text
        url:
            css: 'a.core'
            xpath: null
            type: Link
        image:
            css: 'img.img'
            xpath: null
            type: Attribute
            attribute: data-src
        rating:
            css: 'div.rev'
            xpath: null
            type: Text
        price:
            css: 'div.prc'
            xpath: null
            type: Text
        original_price:
            css: 'div.old'
            xpath: null
            type: Text
        discount:
            css: 'div.bdg._dsct._sm'
            xpath: null
            type: Text
        is_sponsored:
            css: 'div.bdg._spns'
            xpath: null
            type: Text
        delivery_info:
            css: 'div.shpng'
            xpath: null
            type: Text
"""

class JumiaSearchExtractor:
    def __init__(self):
        self._extractor = Extractor.from_yaml_string(YAML_STRING)

    def _scrape(self, url: str, headers: Dict[str, str] = None) -> Dict[str, Any]:
        if not headers:
            headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
                "Connection": "keep-alive",
            }

        response = requests.get(url, headers=headers)

        if response.status_code > 500:
            raise Exception(f"Page {url} was blocked by Jumia. Please try using better proxies.")
        
        return self._extractor.extract(response.text)

    def _process_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        processed = {}
        
        processed['title'] = product.get('title', '').strip()
        processed['url'] = f"https://www.jumia.com{product.get('url', '')}"
        processed['image'] = product.get('image', '')
        
        rating = product.get('rating', '')
        processed['rating'] = float(rating.split(" ")[0]) if rating else None
        
        processed['price'] = product.get('price', '').strip().replace(" ", "")
        processed['source'] = 'Jumia'
        
        return processed

    def search(self, query: str, page: int = 1, headers: Dict[str, str] = None) -> Dict[str, List[Dict[str, Any]]]:
        url = f"https://www.jumia.com.ng/catalog/?q={query}&page={page}"
        raw_data = self._scrape(url, headers)
        
        processed_products = [self._process_product(product) for product in raw_data.get('products', [])]
        
        return {
            "query": query,
            "page": page,
            "products": processed_products
        }

# # Usage example:
# if __name__ == "__main__":
#     extractor = JumiaSearchExtractor()
#     results = extractor.search("laptop", page=1)
    
#     print(f"Found {len(results['products'])} products:")
#     for product in results['products']:
#         print(f"Title: {product['title']}")
#         print(f"Price: {product['price']}")
#         print(f"Rating: {product['rating']}")
#         #print(f"Number of ratings: {product['number_of_ratings']}")
#         print(f"Image URL: {product['image']}")
#         print("-" * 50)
