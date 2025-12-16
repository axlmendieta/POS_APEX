from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import crud
from models import Transaction, TransactionDetail, Product, Location
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_upsell_offer(db: Session, location_id: int, customer_id: int, current_cart_items: list[dict]):
    """
    Analyzes customer habits and current cart to suggest upsells.
    STRICTLY for Proprietary Stores.
    """
    try:
        # --- Step A: Scope Check (Gatekeeper) ---
        location = crud.get_location(db, location_id)
        if not location:
            raise ValueError("Invalid Location.")
            
        if location.location_type != 'store':
            logger.info(f"Upsell aborted: Location {location_id} is not a Proprietary Store.")
            return None

        # --- Step B: Pattern Recognition ---
        
        # 1. Analyze Current Cart & Identify Candidates
        cart_product_ids = [item['product_id'] for item in current_cart_items]
        
        # Strategy 1: Upgrade (Find "Premium" version of item in cart)
        # Simplified Logic: Find product in same category with Higher Price
        for item in current_cart_items:
            current_prod = crud.get_product(db, item['product_id'])
            if not current_prod or not current_prod.category_id:
                continue
                
            # Find expensive sibling
            premium_candidate = db.query(Product).filter(
                Product.category_id == current_prod.category_id,
                Product.price > current_prod.price,
                Product.id.notin_(cart_product_ids) # Not already in cart
            ).order_by(desc(Product.price)).first()
            
            if premium_candidate:
                return _build_offer(premium_candidate, "Upgrade", f"Treat yourself! Upgrade your {current_prod.name} to {premium_candidate.name}.")

        # Strategy 2: Complementary/Favorite (Buy their favorite item if missing)
        # Find most purchased item by this customer
        if customer_id:
            favorite_stats = db.query(
                TransactionDetail.product_id, 
                func.count(TransactionDetail.product_id).label('count')
            ).join(Transaction).filter(
                Transaction.customer_id == customer_id
            ).group_by(
                TransactionDetail.product_id
            ).order_by(desc('count')).all()
            
            for prod_id, count in favorite_stats:
                if prod_id not in cart_product_ids:
                    fav_prod = crud.get_product(db, prod_id)
                    return _build_offer(fav_prod, "Loyalty", f"Don't forget your favorite: {fav_prod.name}!")

        return None # No recommendation found

    except Exception as e:
        logger.error(f"Upsell generation failed: {e}")
        return None

def _build_offer(product: Product, reason_code: str, message: str):
    """
    Helper to construct the JSON offer with dynamic pricing.
    """
    original_price = float(product.price)
    discount_percent = 0.15 # 15% OFF
    special_price = round(original_price * (1 - discount_percent), 2)
    
    return {
        "recommendation_active": True,
        "suggested_product_id": product.id,
        "suggested_product_name": product.name,
        "reason": message,
        "reason_code": reason_code,
        "original_price": original_price,
        "special_offer_price": special_price,
        "promo_tag": f"Just for you: 15% OFF"
    }
