import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
from supabase import create_client, Client
import jwt
import datetime
import uuid
import logging
import json
from werkzeug.security import generate_password_hash, check_password_hash

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("api")

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize Supabase client
supabase_url = "https://cwofeqwdvculjpzeaqem.supabase.co"
supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN3b2ZlcXdkdmN1bGpwemVhcWVtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ3ODc2NjEsImV4cCI6MjA2MDM2MzY2MX0.6JuNOWoL-fRBlY0N-wnNbKzM3Wa0-8DqvqwHcAVOvbE"
supabase = create_client(supabase_url, supabase_key)

# JWT configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Helper functions
def generate_token(user_id):
    """Generate JWT token for user."""
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token):
    """Verify JWT token and return user_id if valid."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload.get("user_id")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_user_from_request():
    """Get user ID from request Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ")[1]
    return verify_token(token)

# API Routes
@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "ok", "message": "API is running"})

# Product routes
@app.route("/api/products", methods=["GET"])
def get_products():
    """Get products with optional filtering."""
    try:
        # Get query parameters
        category = request.args.get("category")
        retailer = request.args.get("retailer")
        search = request.args.get("search")
        discount_only = request.args.get("discount_only", "false").lower() == "true"
        limit = int(request.args.get("limit", 20))
        offset = int(request.args.get("offset", 0))
        
        # Start query
        query = supabase.table("products").select(
            "id, name, image_url, url, retailer_id, category_id, created_at, updated_at"
        )
        
        # Apply filters
        if category:
            query = query.eq("category_id", category)
        
        if retailer:
            query = query.eq("retailer_id", retailer)
        
        if search:
            query = query.ilike("name", f"%{search}%")
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1)
        
        # Execute query
        response = query.execute()
        
        if not response.data:
            return jsonify({"products": [], "total": 0})
        
        products = response.data
        
        # Get prices for each product
        for product in products:
            price_query = supabase.table("product_prices").select(
                "id, regular_price, sale_price, discount_percentage, currency, in_stock, store_id, created_at, updated_at"
            ).eq("product_id", product["id"]).order("created_at", desc=True).limit(1)
            
            price_response = price_query.execute()
            
            if price_response.data:
                product["price"] = price_response.data[0]
            else:
                product["price"] = None
        
        # Filter by discount if requested
        if discount_only:
            products = [p for p in products if p["price"] and p["price"]["discount_percentage"]]
        
        # Get total count
        count_query = supabase.table("products").select("id", count="exact")
        
        if category:
            count_query = count_query.eq("category_id", category)
        
        if retailer:
            count_query = count_query.eq("retailer_id", retailer)
        
        if search:
            count_query = count_query.ilike("name", f"%{search}%")
        
        count_response = count_query.execute()
        total = count_response.count if hasattr(count_response, "count") else len(products)
        
        return jsonify({"products": products, "total": total})
    
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/products/<product_id>", methods=["GET"])
def get_product(product_id):
    """Get product details by ID."""
    try:
        # Get product
        response = supabase.table("products").select(
            "id, name, image_url, url, retailer_id, category_id, created_at, updated_at"
        ).eq("id", product_id).execute()
        
        if not response.data:
            return jsonify({"error": "Product not found"}), 404
        
        product = response.data[0]
        
        # Get retailer
        retailer_response = supabase.table("retailers").select(
            "id, name, website, logo_url"
        ).eq("id", product["retailer_id"]).execute()
        
        if retailer_response.data:
            product["retailer"] = retailer_response.data[0]
        
        # Get category
        if product["category_id"]:
            category_response = supabase.table("categories").select(
                "id, name, parent_id"
            ).eq("id", product["category_id"]).execute()
            
            if category_response.data:
                product["category"] = category_response.data[0]
        
        # Get price history
        price_response = supabase.table("product_prices").select(
            "id, regular_price, sale_price, discount_percentage, currency, in_stock, store_id, created_at, updated_at"
        ).eq("product_id", product_id).order("created_at", desc=True).limit(10).execute()
        
        if price_response.data:
            product["prices"] = price_response.data
            
            # Get store information for each price
            for price in product["prices"]:
                store_response = supabase.table("stores").select(
                    "id, name, location, retailer_id"
                ).eq("id", price["store_id"]).execute()
                
                if store_response.data:
                    price["store"] = store_response.data[0]
        
        # Get similar products
        if product["category_id"]:
            similar_response = supabase.table("products").select(
                "id, name, image_url"
            ).eq("category_id", product["category_id"]).neq("id", product_id).limit(5).execute()
            
            if similar_response.data:
                product["similar_products"] = similar_response.data
        
        return jsonify(product)
    
    except Exception as e:
        logger.error(f"Error getting product {product_id}: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/products/compare", methods=["GET"])
def compare_products():
    """Compare products by IDs."""
    try:
        # Get product IDs from query parameters
        product_ids = request.args.get("ids", "").split(",")
        
        if not product_ids or product_ids[0] == "":
            return jsonify({"error": "No product IDs provided"}), 400
        
        products = []
        
        # Get each product
        for product_id in product_ids:
            response = supabase.table("products").select(
                "id, name, image_url, url, retailer_id, category_id"
            ).eq("id", product_id).execute()
            
            if not response.data:
                continue
            
            product = response.data[0]
            
            # Get retailer
            retailer_response = supabase.table("retailers").select(
                "id, name, logo_url"
            ).eq("id", product["retailer_id"]).execute()
            
            if retailer_response.data:
                product["retailer"] = retailer_response.data[0]
            
            # Get latest price
            price_response = supabase.table("product_prices").select(
                "id, regular_price, sale_price, discount_percentage, currency, store_id"
            ).eq("product_id", product_id).order("created_at", desc=True).limit(1).execute()
            
            if price_response.data:
                product["price"] = price_response.data[0]
                
                # Get store
                store_response = supabase.table("stores").select(
                    "id, name, location"
                ).eq("id", product["price"]["store_id"]).execute()
                
                if store_response.data:
                    product["price"]["store"] = store_response.data[0]
            
            products.append(product)
        
        return jsonify({"products": products})
    
    except Exception as e:
        logger.error(f"Error comparing products: {e}")
        return jsonify({"error": str(e)}), 500

# Category routes
@app.route("/api/categories", methods=["GET"])
def get_categories():
    """Get all categories."""
    try:
        response = supabase.table("categories").select("id, name, parent_id").execute()
        
        if not response.data:
            return jsonify({"categories": []})
        
        categories = response.data
        
        # Organize into hierarchy
        root_categories = []
        category_map = {}
        
        # Create map of categories
        for category in categories:
            category["children"] = []
            category_map[category["id"]] = category
        
        # Build hierarchy
        for category in categories:
            if category["parent_id"]:
                parent = category_map.get(category["parent_id"])
                if parent:
                    parent["children"].append(category)
            else:
                root_categories.append(category)
        
        return jsonify({"categories": root_categories})
    
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return jsonify({"error": str(e)}), 500

# Retailer routes
@app.route("/api/retailers", methods=["GET"])
def get_retailers():
    """Get all retailers."""
    try:
        response = supabase.table("retailers").select("id, name, website, logo_url").execute()
        
        if not response.data:
            return jsonify({"retailers": []})
        
        retailers = response.data
        
        # Get stores for each retailer
        for retailer in retailers:
            stores_response = supabase.table("stores").select(
                "id, name, location, address"
            ).eq("retailer_id", retailer["id"]).execute()
            
            if stores_response.data:
                retailer["stores"] = stores_response.data
        
        return jsonify({"retailers": retailers})
    
    except Exception as e:
        logger.error(f"Error getting retailers: {e}")
        return jsonify({"error": str(e)}), 500

# User routes
@app.route("/api/auth/register", methods=["POST"])
def register():
    """Register a new user."""
    try:
        data = request.json
        
        if not data or not data.get("username") or not data.get("password"):
            return jsonify({"error": "Username and password are required"}), 400
        
        # Check if username already exists
        response = supabase.table("users").select("id").eq("username", data["username"]).execute()
        
        if response.data:
            return jsonify({"error": "Username already exists"}), 409
        
        # Check if email already exists (if provided)
        if data.get("email"):
            response = supabase.table("users").select("id").eq("email", data["email"]).execute()
            
            if response.data:
                return jsonify({"error": "Email already exists"}), 409
        
        # Create user
        user_id = str(uuid.uuid4())
        user_data = {
            "id": user_id,
            "username": data["username"],
            "password_hash": generate_password_hash(data["password"]),
            "email": data.get("email"),
            "first_name": data.get("first_name"),
            "last_name": data.get("last_name")
        }
        
        response = supabase.table("users").insert(user_data).execute()
        
        if not response.data:
            return jsonify({"error": "Failed to create user"}), 500
        
        # Create default watchlist
        watchlist_data = {
            "user_id": user_id,
            "name": "My Watchlist",
            "description": "Default watchlist"
        }
        
        supabase.table("watchlists").insert(watchlist_data).execute()
        
        # Generate token
        token = generate_token(user_id)
        
        return jsonify({
            "token": token,
            "user": {
                "id": user_id,
                "username": data["username"],
                "email": data.get("email"),
                "first_name": data.get("first_name"),
                "last_name": data.get("last_name")
            }
        })
    
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/auth/login", methods=["POST"])
def login():
    """Login a user."""
    try:
        data = request.json
        
        if not data or not data.get("username") or not data.get("password"):
            return jsonify({"error": "Username and password are required"}), 400
        
        # Get user
        response = supabase.table("users").select(
            "id, username, password_hash, email, first_name, last_name"
        ).eq("username", data["username"]).execute()
        
        if not response.data:
            return jsonify({"error": "Invalid username or password"}), 401
        
        user = response.data[0]
        
        # Check password
        if not check_password_hash(user["password_hash"], data["password"]):
            return jsonify({"error": "Invalid username or password"}), 401
        
        # Generate token
        token = generate_token(user["id"])
        
        return jsonify({
            "token": token,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "first_name": user["first_name"],
                "last_name": user["last_name"]
            }
        })
    
    except Exception as e:
        logger.error(f"Error logging in user: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/auth/me", methods=["GET"])
def get_current_user():
    """Get current user information."""
    try:
        user_id = get_user_from_request()
        
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        
        # Get user
        response = supabase.table("users").select(
            "id, username, email, first_name, last_name, created_at, updated_at"
        ).eq("id", user_id).execute()
        
        if not response.data:
            return jsonify({"error": "User not found"}), 404
        
        user = response.data[0]
        
        # Get user's watchlists
        watchlists_response = supabase.table("watchlists").select(
            "id, name, description, created_at, updated_at"
        ).eq("user_id", user_id).execute()
        
        if watchlists_response.data:
            user["watchlists"] = watchlists_response.data
        
        # Get unread notification count
        notifications_response = supabase.table("notifications").select(
            "id", count="exact"
        ).eq("user_id", user_id).eq("is_read", False).execute()
        
        user["unread_notifications"] = notifications_response.count if hasattr(notifications_response, "count") else 0
        
        return jsonify(user)
    
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return jsonify({"error": str(e)}), 500

# Watchlist routes
@app.route("/api/watchlists", methods=["GET"])
def get_watchlists():
    """Get user's watchlists."""
    try:
        user_id = get_user_from_request()
        
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        
        # Get watchlists
        response = supabase.table("watchlists").select(
            "id, name, description, created_at, updated_at"
        ).eq("user_id", user_id).execute()
        
        if not response.data:
            return jsonify({"watchlists": []})
        
        watchlists = response.data
        
        # Get items count for each watchlist
        for watchlist in watchlists:
            items_response = supabase.table("watchlist_items").select(
                "id", count="exact"
            ).eq("watchlist_id", watchlist["id"]).execute()
            
            watchlist["items_count"] = items_response.count if hasattr(items_response, "count") else 0
        
        return jsonify({"watchlists": watchlists})
    
    except Exception as e:
        logger.error(f"Error getting watchlists: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/watchlists", methods=["POST"])
def create_watchlist():
    """Create a new watchlist."""
    try:
        user_id = get_user_from_request()
        
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        
        data = request.json
        
        if not data or not data.get("name"):
            return jsonify({"error": "Watchlist name is required"}), 400
        
        # Create watchlist
        watchlist_data = {
            "user_id": user_id,
            "name": data["name"],
            "description": data.get("description")
        }
        
        response = supabase.table("watchlists").insert(watchlist_data).execute()
        
        if not response.data:
            return jsonify({"error": "Failed to create watchlist"}), 500
        
        return jsonify(response.data[0])
    
    except Exception as e:
        logger.error(f"Error creating watchlist: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/watchlists/<watchlist_id>/items", methods=["GET"])
def get_watchlist_items(watchlist_id):
    """Get items in a watchlist."""
    try:
        user_id = get_user_from_request()
        
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        
        # Check if watchlist belongs to user
        watchlist_response = supabase.table("watchlists").select("id").eq("id", watchlist_id).eq("user_id", user_id).execute()
        
        if not watchlist_response.data:
            return jsonify({"error": "Watchlist not found"}), 404
        
        # Get watchlist items
        items_response = supabase.table("watchlist_items").select(
            "id, product_id, price_threshold, created_at, updated_at"
        ).eq("watchlist_id", watchlist_id).execute()
        
        if not items_response.data:
            return jsonify({"items": []})
        
        items = items_response.data
        
        # Get product details for each item
        for item in items:
            product_response = supabase.table("products").select(
                "id, name, image_url, url, retailer_id, category_id"
            ).eq("id", item["product_id"]).execute()
            
            if product_response.data:
                item["product"] = product_response.data[0]
                
                # Get retailer
                retailer_response = supabase.table("retailers").select(
                    "id, name, logo_url"
                ).eq("id", item["product"]["retailer_id"]).execute()
                
                if retailer_response.data:
                    item["product"]["retailer"] = retailer_response.data[0]
                
                # Get latest price
                price_response = supabase.table("product_prices").select(
                    "id, regular_price, sale_price, discount_percentage, currency, store_id, created_at"
                ).eq("product_id", item["product_id"]).order("created_at", desc=True).limit(1).execute()
                
                if price_response.data:
                    item["product"]["price"] = price_response.data[0]
                    
                    # Get store
                    store_response = supabase.table("stores").select(
                        "id, name, location"
                    ).eq("id", item["product"]["price"]["store_id"]).execute()
                    
                    if store_response.data:
                        item["product"]["price"]["store"] = store_response.data[0]
        
        return jsonify({"items": items})
    
    except Exception as e:
        logger.error(f"Error getting watchlist items: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/watchlists/<watchlist_id>/items", methods=["POST"])
def add_watchlist_item(watchlist_id):
    """Add item to watchlist."""
    try:
        user_id = get_user_from_request()
        
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        
        # Check if watchlist belongs to user
        watchlist_response = supabase.table("watchlists").select("id").eq("id", watchlist_id).eq("user_id", user_id).execute()
        
        if not watchlist_response.data:
            return jsonify({"error": "Watchlist not found"}), 404
        
        data = request.json
        
        if not data or not data.get("product_id"):
            return jsonify({"error": "Product ID is required"}), 400
        
        # Check if product exists
        product_response = supabase.table("products").select("id").eq("id", data["product_id"]).execute()
        
        if not product_response.data:
            return jsonify({"error": "Product not found"}), 404
        
        # Check if item already exists in watchlist
        item_response = supabase.table("watchlist_items").select("id").eq("watchlist_id", watchlist_id).eq("product_id", data["product_id"]).execute()
        
        if item_response.data:
            return jsonify({"error": "Product already in watchlist"}), 409
        
        # Add item to watchlist
        item_data = {
            "watchlist_id": watchlist_id,
            "product_id": data["product_id"],
            "price_threshold": data.get("price_threshold")
        }
        
        response = supabase.table("watchlist_items").insert(item_data).execute()
        
        if not response.data:
            return jsonify({"error": "Failed to add item to watchlist"}), 500
        
        return jsonify(response.data[0])
    
    except Exception as e:
        logger.error(f"Error adding item to watchlist: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/watchlists/<watchlist_id>/items/<item_id>", methods=["DELETE"])
def remove_watchlist_item(watchlist_id, item_id):
    """Remove item from watchlist."""
    try:
        user_id = get_user_from_request()
        
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        
        # Check if watchlist belongs to user
        watchlist_response = supabase.table("watchlists").select("id").eq("id", watchlist_id).eq("user_id", user_id).execute()
        
        if not watchlist_response.data:
            return jsonify({"error": "Watchlist not found"}), 404
        
        # Check if item exists
        item_response = supabase.table("watchlist_items").select("id").eq("id", item_id).eq("watchlist_id", watchlist_id).execute()
        
        if not item_response.data:
            return jsonify({"error": "Item not found"}), 404
        
        # Remove item
        supabase.table("watchlist_items").delete().eq("id", item_id).execute()
        
        return jsonify({"success": True})
    
    except Exception as e:
        logger.error(f"Error removing item from watchlist: {e}")
        return jsonify({"error": str(e)}), 500

# Notification routes
@app.route("/api/notifications", methods=["GET"])
def get_notifications():
    """Get user's notifications."""
    try:
        user_id = get_user_from_request()
        
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        
        # Get query parameters
        unread_only = request.args.get("unread_only", "false").lower() == "true"
        limit = int(request.args.get("limit", 20))
        offset = int(request.args.get("offset", 0))
        
        # Start query
        query = supabase.table("notifications").select(
            "id, product_id, message, is_read, created_at"
        ).eq("user_id", user_id).order("created_at", desc=True)
        
        if unread_only:
            query = query.eq("is_read", False)
        
        # Apply pagination
        query = query.range(offset, offset + limit - 1)
        
        # Execute query
        response = query.execute()
        
        if not response.data:
            return jsonify({"notifications": [], "total": 0})
        
        notifications = response.data
        
        # Get product details for each notification
        for notification in notifications:
            if notification["product_id"]:
                product_response = supabase.table("products").select(
                    "id, name, image_url, retailer_id"
                ).eq("id", notification["product_id"]).execute()
                
                if product_response.data:
                    notification["product"] = product_response.data[0]
                    
                    # Get retailer
                    retailer_response = supabase.table("retailers").select(
                        "id, name, logo_url"
                    ).eq("id", notification["product"]["retailer_id"]).execute()
                    
                    if retailer_response.data:
                        notification["product"]["retailer"] = retailer_response.data[0]
        
        # Get total count
        count_query = supabase.table("notifications").select("id", count="exact").eq("user_id", user_id)
        
        if unread_only:
            count_query = count_query.eq("is_read", False)
        
        count_response = count_query.execute()
        total = count_response.count if hasattr(count_response, "count") else len(notifications)
        
        return jsonify({"notifications": notifications, "total": total})
    
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/notifications/mark-read", methods=["POST"])
def mark_notifications_read():
    """Mark notifications as read."""
    try:
        user_id = get_user_from_request()
        
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        
        data = request.json
        
        if data and data.get("notification_ids"):
            # Mark specific notifications as read
            for notification_id in data["notification_ids"]:
                supabase.table("notifications").update({"is_read": True}).eq("id", notification_id).eq("user_id", user_id).execute()
        else:
            # Mark all notifications as read
            supabase.table("notifications").update({"is_read": True}).eq("user_id", user_id).execute()
        
        return jsonify({"success": True})
    
    except Exception as e:
        logger.error(f"Error marking notifications as read: {e}")
        return jsonify({"error": str(e)}), 500

# Deals routes
@app.route("/api/deals", methods=["GET"])
def get_deals():
    """Get current deals."""
    try:
        # Get query parameters
        min_discount = float(request.args.get("min_discount", 10))
        category = request.args.get("category")
        retailer = request.args.get("retailer")
        limit = int(request.args.get("limit", 20))
        offset = int(request.args.get("offset", 0))
        
        # Get products with discounts
        products_query = supabase.table("products").select(
            "id, name, image_url, url, retailer_id, category_id"
        )
        
        if category:
            products_query = products_query.eq("category_id", category)
        
        if retailer:
            products_query = products_query.eq("retailer_id", retailer)
        
        products_response = products_query.execute()
        
        if not products_response.data:
            return jsonify({"deals": [], "total": 0})
        
        products = products_response.data
        deals = []
        
        # Get latest price for each product
        for product in products:
            price_response = supabase.table("product_prices").select(
                "id, regular_price, sale_price, discount_percentage, currency, store_id, created_at"
            ).eq("product_id", product["id"]).order("created_at", desc=True).limit(1).execute()
            
            if price_response.data and price_response.data[0]["discount_percentage"] and price_response.data[0]["discount_percentage"] >= min_discount:
                product["price"] = price_response.data[0]
                
                # Get retailer
                retailer_response = supabase.table("retailers").select(
                    "id, name, logo_url"
                ).eq("id", product["retailer_id"]).execute()
                
                if retailer_response.data:
                    product["retailer"] = retailer_response.data[0]
                
                # Get store
                store_response = supabase.table("stores").select(
                    "id, name, location"
                ).eq("id", product["price"]["store_id"]).execute()
                
                if store_response.data:
                    product["price"]["store"] = store_response.data[0]
                
                deals.append(product)
        
        # Sort by discount percentage (highest first)
        deals.sort(key=lambda x: x["price"]["discount_percentage"] or 0, reverse=True)
        
        # Apply pagination
        paginated_deals = deals[offset:offset + limit]
        
        return jsonify({"deals": paginated_deals, "total": len(deals)})
    
    except Exception as e:
        logger.error(f"Error getting deals: {e}")
        return jsonify({"error": str(e)}), 500

# Start server
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
