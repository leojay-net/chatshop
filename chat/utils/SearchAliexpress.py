from selectorlib import Extractor
import requests
import re
from typing import Dict, List, Any
import time

YAML_STRING = """
products:
    css: 'div.search-item-card-wrapper-gallery'
    xpath: null
    multiple: true
    type: Text
    children:
        title:
            css: 'h3.multi--titleText--nXeOvyr'
            xpath: null
            type: Text
        url:
            css: 'a.multi--container--1UZxxHY'
            xpath: null
            type: Link
        image:
            css: 'img.images--item--3XZa6xf'
            xpath: null
            type: Attribute
            attribute: src
        rating:
            css: 'span.multi--starRating--3cN4Lu6'
            xpath: null
            type: Text
        star_divs:
            css: 'div.multi--progress--2E4WzbQ'
            xpath: null
            multiple: true
            type: HTML
        number_of_ratings:
            css: 'span.multi--trade--Ktbl2jB'
            xpath: null
            type: Text
        price:
            css: 'div.multi--price-sale--U-S0jtj'
            xpath: null
            type: Text
        original_price:
            css: 'div.multi--price-original--1zEQqOK'
            xpath: null
            type: Text
        discount:
            css: 'span.multi--discount--1Bn8G39'
            xpath: null
            type: Text
        shipping:
            css: 'span.multi--price-ship--2ZycSt0'
            xpath: null
            type: Text
        store_name:
            css: 'a.cards--storeLink--XkKUQFS'
            xpath: null
            type: Text
"""

class AliExpressSearchExtractor:
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
            raise Exception(f"Page {url} was blocked. Please try using better proxies.")
        
        return self._extractor.extract(response.text)

    def _process_product(self, product: Dict[str, Any]) -> Dict[str, Any]:
        processed = {}
        
        processed['title'] = product.get('title', '').strip()
        url = product.get('url', '')
        processed['url'] = f"https:{url}" if url else None
        img_url = product.get('image', '')
        processed['image'] = f"https:{img_url}" if img_url else None
        
        star_divs = product.get('star_divs')
        if star_divs and isinstance(star_divs, list):
            try:
                full_stars = len([div for div in star_divs if 'width:10px' in div])
                partial_star = 0
                for div in star_divs:
                    match = re.search(r'width:([\d.]+)px', div)
                    if match and float(match.group(1)) < 10:
                        partial_star = float(match.group(1)) / 10
                        break
                processed['rating'] = round(float(full_stars + partial_star), 1)
            except Exception as e:
                print(f"Error processing star rating: {e}")
                processed['rating'] = None
        else:
            processed['rating'] = None
        
        num_ratings = product.get('number_of_ratings', '')
        try:
            processed['number_of_ratings'] = int(num_ratings.split(" ")[0].replace("+","").strip()) if num_ratings else None
        except ValueError:
            processed['number_of_ratings'] = None
        
        processed['price'] = product.get('price', '').strip().replace(" ", "")
        processed['shipping'] = product.get('shipping', '')
        processed['source'] = 'Aliexpress'

        
        return processed

    def search(self, query: str, page: int = 1, headers: Dict[str, str] = None) -> Dict[str, List[Dict[str, Any]]]:
        url = f"https://www.aliexpress.com/wholesale?SearchText={query}&page={page}"
        raw_data = self._scrape(url, headers)
        
        processed_products = [self._process_product(product) for product in raw_data.get('products', [])]
        
        return {
            "query": query,
            "page": page,
            "products": processed_products
        }

# # Usage example:
# if __name__ == "__main__":
#     extractor = AliExpressSearchExtractor()
#     results = extractor.search("laptop", page=1)
    
#     print(f"Found {len(results['products'])} products:")
#     for product in results['products']:
#         print(f"Title: {product['title']}")
#         print(f"URL: {product['url']}")
#         print(f"Price: {product['price']}")
#         print(f"Rating: {product['rating']}")
#         print(f"Number of ratings: {product['number_of_ratings']}")
#         print(f"Image URL: {product['image']}")
#         print(f"Shipping: {product['shipping']}")
#         print("-" * 50)