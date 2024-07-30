import time
import re
from operator import itemgetter
from .SearchAmazon import AmazonSearchExtractor
from .SearchAliexpress import AliExpressSearchExtractor
from .SearchJumia import JumiaSearchExtractor

class MultiPlatformSearcher:
    def __init__(self):
        self.extractors = [
            AmazonSearchExtractor(),
            AliExpressSearchExtractor(),
            JumiaSearchExtractor()
        ]

    def search_and_sort_products(self, query, num_pages=3, sort_criteria=[('price', False), ('rating', True)]):
        all_products = []

        for extractor in self.extractors:
            for page in range(1, num_pages + 1):
                print(f"Searching {extractor.__class__.__name__} page {page}...")
                try:
                    results = extractor.search(query, page)
                    all_products.extend(results['products'])
                except Exception as e:
                    print(f"Error searching {extractor.__class__.__name__} page {page}: {e}")
                time.sleep(2)  # Add a delay to avoid overwhelming the server

        # Remove products with missing data for any of the sort fields
        filtered_products = [p for p in all_products if all(field in p and p[field] is not None for field, _ in sort_criteria)]

        # Prepare the products for sorting
        for product in filtered_products:
            for field, _ in sort_criteria:
                if field == 'price':
                    product[f'{field}_sort'] = float(re.sub(r'[^\d.]', '', product[field]))
                elif field in ['rating', 'number_of_ratings']:
                    product[f'{field}_sort'] = float(product[field]) if product[field] else 0
                else:
                    product[f'{field}_sort'] = product[field]

        # Sort the products
        for field, reverse in reversed(sort_criteria):
            filtered_products.sort(key=itemgetter(f'{field}_sort'), reverse=reverse)

        return filtered_products

    # @staticmethod
    # def print_product(product):
    #     print(f"Title: {product['title']}")
    #     print(f"Price: {product['price']}")
    #     print(f"Rating: {product['rating']}")
    #     print(f"Number of Ratings: {product['number_of_ratings']}" or f'Number of Ratings: {None}')
    #     print(f"URL: {product['url']}")
    #     print(f"Image URL: {product['image']}")
    #     print(f"Source: {product.get('source', 'Unknown')}")
    #     print("-" * 50)


# if __name__ == "__main__":
#     start = time.time()
#     searcher = MultiPlatformSearcher()
    
#     query = input("Enter your search query: ")
#     num_pages = int(input("Enter the number of pages to search per site (default 3): ") or 3)
    
#     # Example sort criteria: first by price (ascending), then by rating (descending)
#     sort_criteria = [('price', False), ('rating', True)]
    
#     products = searcher.search_and_sort_products(query, num_pages, sort_criteria)
#     print(products)
#     stop = time.time()
#     print(f"\nFound {len(products)} products. Sorted by multiple criteria: {sort_criteria}")
#     print("\n\nTIME_TAKEN: ", stop-start, "\n\n")
#     for product in products[:10]:  # Print top 10 results
#         MultiPlatformSearcher.print_product(product)

#     print(f"Total products: {len(products)}")