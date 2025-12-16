from database import SessionLocal
from init_db import init_db
import crud
import service_logic

def test_service_logic():
    print("Initializing Database...")
    init_db()
    db = SessionLocal()
    
    try:
        # Setup Data
        print("\n--- Setup Data ---")
        cat = crud.create_category(db, "Service Test Cat")
        prod = crud.create_product(db, "Service Test Prod", 100.0, cat.id)
        loc = crud.create_location(db, "Service Store", "store")
        emp = crud.create_employee(db, "seller", "cashier", "pass", loc.id)
        
        # Initialize Stock: 10 units
        crud.update_stock(db, loc.id, prod.id, 10)
        print("Initial Stock: 10")

        # 1. Test Successful Sale
        print("\n--- Test 1: Successful Sale (Quantity 5) ---")
        items_success = [{'product_id': prod.id, 'quantity': 5, 'unit_price': 100.0}]
        trans = service_logic.process_sale(db, loc.id, emp.id, items_success)
        
        # Verify Results
        stock = crud.get_stock_level(db, loc.id, prod.id)
        print(f"Transaction Created: ID {trans.id}")
        print(f"Remaining Stock: {stock.current_stock}")
        
        assert stock.current_stock == 5
        assert trans is not None
        print("SUCCESS: Sale processed and stock updated.")

        # 2. Test Insufficient Stock (Atomicity Rollback)
        print("\n--- Test 2: Insufficient Stock (Request 10, Have 5) ---")
        items_fail = [{'product_id': prod.id, 'quantity': 10, 'unit_price': 100.0}]
        
        try:
            service_logic.process_sale(db, loc.id, emp.id, items_fail)
            print("ERROR: Sale should have failed but didn't!")
        except ValueError as e:
            print(f"Expected Error Caught: {e}")
            
        # Verify Rollback (Stock should still be 5, not -5 or something else)
        # Note: We need a new session or refresh to be sure we aren't seeing stale data if using same session
        db.expire_all() 
        stock_after_fail = crud.get_stock_level(db, loc.id, prod.id)
        print(f"Stock after failed sale: {stock_after_fail.current_stock}")
        
        assert stock_after_fail.current_stock == 5
        print("SUCCESS: Transaction rolled back, stock remains consistent.")

        print("\nALL SERVICE TESTS PASSED!")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"TEST FAILED: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_service_logic()
