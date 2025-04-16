import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client
import requests
from bs4 import BeautifulSoup
import time
import logging
from datetime import datetime
import uuid

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("lulu_scraper")

class LuluScraper:
    """Scraper for Lulu Hypermarket Oman."""
    
    def __init__(self, supabase: Client):
        """
        Initialize the Lulu scraper.
        
        Args:
            supabase: Supabase client
        """
        self.base_url = "https://www.luluhypermarket.com/en-om"
        self.supabase = supabase
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        # Get retailer ID
        self.retailer_id = self._get_retailer_id("Lulu Hypermarket")
        if not self.retailer_id:
            logger.error("Lulu Hypermarket retailer not found in database")
    
    def _get_retailer_id(self, retailer_name):
        """Get retailer ID from database."""
        try:
            response = self.supabase.table("retailers").select("id").eq("name", retailer_name).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]["id"]
            return None
        except Exception as e:
            logger.error(f"Error getting retailer ID: {e}")
            return None
    
    def _get_store_id(self, store_name):
        """Get store ID from database."""
        try:
            response = self.supabase.table("stores").select("id").eq("name", store_name).eq("retailer_id", self.retailer_id).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]["id"]
            
            # If store doesn't exist, create it
            store_data = {
                "retailer_id": self.retailer_id,
                "name": store_name,
                "location": store_name.split(" ")[-1]
            }
            response = self.supabase.table("stores").insert(store_data).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]["id"]
            
            return None
        except Exception as e:
            logger.error(f"Error getting/creating store ID: {e}")
            return None
    
    def _get_category_id(self, category_name):
        """Get category ID from database."""
        try:
            response = self.supabase.table("categories").select("id").eq("name", category_name).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]["id"]
            
            # If category doesn't exist, create it
            category_data = {
                "name": category_name
            }
            response = self.supabase.table("categories").insert(category_data).execute()
            if response.data and len(response.data) > 0:
                return response.data[0]["id"]
            
            return None
        except Exception as e:
            logger.error(f"Error getting/creating category ID: {e}")
            return None
    
    def get_categories(self, max_categories=None):
        """
        Get categories from Lulu Hypermarket.
        
        Args:
            max_categories: Maximum number of categories to return
            
        Returns:
            list: List of category URLs
        """
        try:
            logger.info("Getting categories from Lulu Hypermarket")
            response = requests.get(self.base_url, headers=self.headers)
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Find category links
            category_links = []
            nav_items = soup.select(".nav-item .nav-link")
            
            for item in nav_items:
                href = item.get("href")
                if href and "/c/" in href and href not in category_links:
                    category_links.append(href)
            
            # Add base URL if needed
            category_urls = []
            for link in category_links:
                if link.startswith("/"):
                    category_urls.append(self.base_url + link)
                else:
                    category_urls.append(link)
            
            if max_categories:
                category_urls = category_urls[:max_categories]
            
            logger.info(f"Found {len(category_urls)} categories")
            return category_urls
        
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    def scrape_category(self, category_url, max_pages=3):
        """
        Scrape products from a category.
        
        Args:
            category_url: Category URL
            max_pages: Maximum number of pages to scrape
            
        Returns:
            list: List of product dictionaries
        """
        try:
            logger.info(f"Scraping category: {category_url}")
            products = []
            
            # Extract category name from URL
            category_name = category_url.split("/")[-1].replace("-", " ").title()
            category_id = self._get_category_id(category_name)
            
            # Get first page
            response = requests.get(category_url, headers=self.headers)
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extract products from first page
            products.extend(self._extract_products(soup, category_id))
            
            # Check if there are more pages
            pagination = soup.select(".pagination .page-item")
            if pagination and len(pagination) > 2:
                # Determine number of pages
                last_page = min(max_pages, int(pagination[-2].text.strip()))
                
                # Scrape additional pages
                for page in range(2, last_page + 1):
                    page_url = f"{category_url}?page={page}"
                    logger.info(f"Scraping page {page}: {page_url}")
                    
                    try:
                        response = requests.get(page_url, headers=self.headers)
                        soup = BeautifulSoup(response.text, "html.parser")
                        products.extend(self._extract_products(soup, category_id))
                        
                        # Sleep to avoid rate limiting
                        time.sleep(1)
                    
                    except Exception as e:
                        logger.error(f"Error scraping page {page}: {e}")
            
            logger.info(f"Found {len(products)} products in category {category_name}")
            return products
        
        except Exception as e:
            logger.error(f"Error scraping category {category_url}: {e}")
            return []
    
    def _extract_products(self, soup, category_id):
        """
        Extract products from a page.
        
        Args:
            soup: BeautifulSoup object
            category_id: Category ID
            
        Returns:
            list: List of product dictionaries
        """
        products = []
        
        # Get store ID for Lulu Muscat
        store_id = self._get_store_id("Lulu Hypermarket Muscat")
        if not store_id:
            logger.error("Could not get store ID")
            return products
        
        # Find product items
        product_items = soup.select(".product-item")
        
        for item in product_items:
            try:
                # Extract product details
                name_elem = item.select_one(".product-name")
                name = name_elem.text.strip() if name_elem else "Unknown Product"
                
                url_elem = item.select_one("a.product-link")
                url = url_elem.get("href") if url_elem else None
                if url and url.startswith("/"):
                    url = self.base_url + url
                
                image_elem = item.select_one(".product-image img")
                image_url = image_elem.get("src") if image_elem else None
                
                # Extract price information
                price_elem = item.select_one(".product-price")
                regular_price = None
                sale_price = None
                discount_percentage = None
                
                if price_elem:
                    # Check for discount
                    old_price_elem = price_elem.select_one(".old-price")
                    if old_price_elem:
                        # Product is on sale
                        old_price_text = old_price_elem.text.strip()
                        regular_price = float(old_price_text.replace("OMR", "").strip())
                        
                        new_price_elem = price_elem.select_one(".new-price")
                        if new_price_elem:
                            new_price_text = new_price_elem.text.strip()
                            sale_price = float(new_price_text.replace("OMR", "").strip())
                            
                            # Calculate discount percentage
                            if regular_price > 0:
                                discount_percentage = ((regular_price - sale_price) / regular_price) * 100
                    else:
                        # Regular price (no discount)
                        price_text = price_elem.text.strip()
                        regular_price = float(price_text.replace("OMR", "").strip())
                        sale_price = regular_price
                
                # Create product in database if it doesn't exist
                product_data = {
                    "name": name,
                    "retailer_id": self.retailer_id,
                    "category_id": category_id,
                    "image_url": image_url,
                    "url": url
                }
                
                # Check if product exists
                response = self.supabase.table("products").select("id").eq("name", name).eq("retailer_id", self.retailer_id).execute()
                
                if response.data and len(response.data) > 0:
                    # Product exists, update it
                    product_id = response.data[0]["id"]
                    self.supabase.table("products").update(product_data).eq("id", product_id).execute()
                else:
                    # Create new product
                    response = self.supabase.table("products").insert(product_data).execute()
                    if not (response.data and len(response.data) > 0):
                        logger.error(f"Failed to create product: {name}")
                        continue
                    product_id = response.data[0]["id"]
                
                # Add price information
                if sale_price is not None:
                    price_data = {
                        "product_id": product_id,
                        "store_id": store_id,
                        "regular_price": regular_price,
                        "sale_price": sale_price,
                        "discount_percentage": discount_percentage,
                        "currency": "OMR",
                        "in_stock": True
                    }
                    
                    # Add to database
                    self.supabase.table("product_prices").insert(price_data).execute()
                
                # Add to results
                products.append({
                    "id": product_id,
                    "name": name,
                    "url": url,
                    "image_url": image_url,
                    "regular_price": regular_price,
                    "sale_price": sale_price,
                    "discount_percentage": discount_percentage,
                    "currency": "OMR",
                    "store_id": store_id,
                    "category_id": category_id
                })
            
            except Exception as e:
                logger.error(f"Error extracting product: {e}")
        
        return products
    
    def run(self, max_categories=None, max_pages=3):
        """
        Run the scraper.
        
        Args:
            max_categories: Maximum number of categories to scrape
            max_pages: Maximum number of pages per category
            
        Returns:
            list: List of scraped products
        """
        all_products = []
        
        # Get categories
        categories = self.get_categories(max_categories)
        
        # Scrape each category
        for category_url in categories:
            products = self.scrape_category(category_url, max_pages)
            all_products.extend(products)
            
            # Sleep to avoid rate limiting
            time.sleep(2)
        
        logger.info(f"Scraped {len(all_products)} products in total")
        return all_products


if __name__ == "__main__":
    # Initialize Supabase client
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("SUPABASE_URL and SUPABASE_KEY environment variables must be set")
        exit(1)
    
    supabase = create_client(supabase_url, supabase_key)
    
    # Run scraper
    scraper = LuluScraper(supabase)
    products = scraper.run(max_categories=3, max_pages=2)
    
    # Print results
    print(f"Scraped {len(products)} products")
