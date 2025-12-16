import init_db
from database import SessionLocal
import crud
import service_logic
import os
import traceback

def setup_db():
    os.environ["ALLOW_SCHEMA_DROP"] = "true"
    init_db.init_db()
    os.environ.pop("ALLOW_SCHEMA_DROP", None)

def test_multitenant_logic():
    print("\n--- Test: Multi-Tenant Replenishment ---")
    setup_db()
    db = SessionLocal()
    try:
        # Setup Data
        hq = crud.create_location(db, "HQ Warehouse", "warehouse")
        store = crud.create_location(db, "Internal Store", "store")
        partner = crud.create_location(db, "Wholesale Partner", "partner")
        
        emp_admin = crud.create_employee(db, "admin", "logistics_manager", "pwd", hq.id)

        # Product with Wholesale Price
        # Retail: $10, Wholesale: $8, Cost: $5
        prod = crud.create_product(db, "Soda", 10.0, barcode="123", cost_price=5.0, wholesale_price=8.0)
        
        # Initial Stock at HQ: 1000
        crud.update_stock(db, hq.id, prod.id, 1000)
        db.commit()
        
        # --- Scenario 1: Internal Replenishment (Transfer) ---
        print("Scenario 1: Sending 50 to Internal Store (Should be Transfer)...")
        items = [{'product_id': prod.id, 'quantity': 50}]
        
        res = service_logic.process_replenishment(db, hq.id, store.id, items, emp_admin.id)
        assert res['type'] == 'transfer'
        print("SUCCESS: Identified as Transfer.")
        
        # Verify Stock Movement
        hq_stock = crud.get_stock_level(db, hq.id, prod.id)
        store_stock = crud.get_stock_level(db, store.id, prod.id)
        print(f"HQ Stock: {hq_stock.current_stock} (Expected 950)")
        print(f"Store Stock: {store_stock.current_stock} (Expected 50)")
        assert hq_stock.current_stock == 950
        assert store_stock.current_stock == 50
        
        # --- Scenario 2: External Replenishment (Wholesale Order) ---
        print("\nScenario 2: Sending 100 to Partner (Should be Sale)...")
        items_wh = [{'product_id': prod.id, 'quantity': 100}]
        
        res_wh = service_logic.process_replenishment(db, hq.id, partner.id, items_wh, emp_admin.id)
        assert res_wh['type'] == 'sale'
        print("SUCCESS: Identified as Sale.")
        
        # Verify Stock Movement
        db.refresh(hq_stock)
        partner_stock = crud.get_stock_level(db, partner.id, prod.id)
        
        print(f"HQ Stock: {hq_stock.current_stock} (Expected 850)")
        print(f"Partner Stock: {partner_stock.current_stock} (Expected 100)")
        assert hq_stock.current_stock == 850
        assert partner_stock.current_stock == 100
        
        # Verify Price Logic (Wholesale Price Used)
        tx = res_wh['data']
        detail = tx.details[0]
        print(f"Sale Unit Price: {detail.unit_price} (Expected 8.00)")
        assert float(detail.unit_price) == 8.0
        
        print(f"Total Sale Revenue: {tx.total_amount} (Expected 800.00)")
        assert float(tx.total_amount) == 800.0

        print("SUCCESS: Multi-Tenant Logic Verified.")

    except Exception:
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_multitenant_logic()
