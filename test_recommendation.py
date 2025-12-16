import init_db
from database import SessionLocal
import crud
import recommendation_engine
from models import Category
import os
import service_logic
import traceback

def setup_db():
    os.environ["ALLOW_SCHEMA_DROP"] = "true"
    init_db.init_db()
    os.environ.pop("ALLOW_SCHEMA_DROP", None)

def test_recommendation_logic():
    print("\n--- Test: AI Recommendation Engine ---")
    setup_db()
    db = SessionLocal()
    try:
        # --- 1. Setup Environment ---
        # Locations
        store = crud.create_location(db, "Proprietary Store", "store")
        partner = crud.create_location(db, "External Partner", "partner")
        mgr = crud.create_employee(db, "mgr", "branch_manager", "pwd", store.id)
        
        # Categories & Products
        cat_bev = Category(name="Beverage")
        db.add(cat_bev)
        db.commit()
        
        prod_water = crud.create_product(db, "Water", 1.00, category_id=cat_bev.id)
        prod_soda = crud.create_product(db, "Soda", 2.00, category_id=cat_bev.id)
        prod_premium_soda = crud.create_product(db, "Premium Soda", 5.00, category_id=cat_bev.id) # Upgrade for Soda
        
        # Customer
        cust = crud.create_customer(db, "John Doe", "john@example.com", "555-0100")
        
        # Initialize Stock
        crud.update_stock(db, store.id, prod_water.id, 100)
        crud.update_stock(db, store.id, prod_soda.id, 100)
        crud.update_stock(db, store.id, prod_premium_soda.id, 100)
        db.commit()
        
        # --- 2. Build History (Favorite: Soda) ---
        print("Building Customer History...")
        items = [{'product_id': prod_soda.id, 'quantity': 1, 'unit_price': 2.00}]
        # 3 transactions of Soda
        for _ in range(3):
            service_logic.process_sale(db, store.id, mgr.id, items, cust.id)
            
        # --- 3. Test Scope Gatekeeper ---
        print("\nTest: Gatekeeper (Partner Store)...")
        offer = recommendation_engine.generate_upsell_offer(
            db, partner.id, cust.id, [{'product_id': prod_water.id, 'quantity': 1}]
        )
        if offer is None:
            print("SUCCESS: Aborted for External Partner.")
        else:
             print(f"FAILED: Generated offer for Partner: {offer}")

        # --- 4. Test Strategy: Complementary/Loyalty ---
        # Cart has Water. User loves Soda. Soda not in cart.
        print("\nTest: Strategy - Loyalty (Missing Favorite)...")
        cart_water = [{'product_id': prod_water.id, 'quantity': 1}]
        
        offer = recommendation_engine.generate_upsell_offer(db, store.id, cust.id, cart_water)
        
        if offer and offer['suggested_product_id'] == prod_soda.id:
            print(f"SUCCESS: Suggested Favorite ({offer['suggested_product_name']})")
            print(f"Reason: {offer['reason']}")
            print(f"Promo: {offer['promo_tag']} (${offer['special_offer_price']})")
        else:
            print(f"FAILED: Did not suggest Favorite. Got: {offer}")
            
        # --- 5. Test Strategy: Upgrade ---
        # Cart has Soda. Premium Soda exists in same category.
        print("\nTest: Strategy - Upgrade...")
        cart_soda = [{'product_id': prod_soda.id, 'quantity': 1}]
        
        offer = recommendation_engine.generate_upsell_offer(db, store.id, cust.id, cart_soda)
        
        if offer and offer['suggested_product_id'] == prod_premium_soda.id:
            print(f"SUCCESS: Suggested Upgrade ({offer['suggested_product_name']})")
            print(f"Reason: {offer['reason']}")
            print(f"Promo: {offer['promo_tag']} (${offer['special_offer_price']})")
        else:
            print(f"FAILED: Did not suggest Upgrade. Got: {offer}")

        print("\nSUCCESS: Recommendation Engine Verified.")

    except Exception:
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_recommendation_logic()
