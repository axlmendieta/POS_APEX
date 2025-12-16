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

def test_void_item():
    setup_db()
    db = SessionLocal()
    try:
        # Setup Data
        store_A = crud.create_location(db, "Store A", "store")
        manager_A = crud.create_employee(db, "manager_a", "branch_manager", "pwd", store_A.id)
        cashier_A = crud.create_employee(db, "cashier_a", "internal_cashier", "pwd", store_A.id)
        prod = crud.create_product(db, "Void Item", 50.0)
        
        crud.update_stock(db, store_A.id, prod.id, 100) 
        db.commit() 
        
        # Create Sale (5 items @ $50 = $250)
        print("Creating Sale (5 items)...")
        items = [{'product_id': prod.id, 'quantity': 5, 'unit_price': 50.0}]
        tx = service_logic.process_sale(db, store_A.id, cashier_A.id, items)
        tx_id = tx.id
        
        # Verify Initial State
        stock = crud.get_stock_level(db, store_A.id, prod.id)
        print(f"Stock Initial: {stock.current_stock}") # 95
        assert stock.current_stock == 95
        assert tx.total_amount == 250.0

        # --- Void Partial (Removing 2 items) ---
        print("\nVoiding 2 items (Supervisor)...")
        
        # Fail (Cashier)
        try:
            service_logic.void_line_item(db, tx_id, prod.id, 2, cashier_A.id)
            print("FAILED: Cashier NOT blocked")
        except PermissionError:
            print("SUCCESS: Cashier blocked")
            db.rollback()

        # Success (Manager)
        updated_tx = service_logic.void_line_item(db, tx_id, prod.id, 2, manager_A.id)
        
        # Verify Updates
        db.refresh(stock)
        print(f"Stock after void: {stock.current_stock}") # Should be 95 + 2 = 97
        assert stock.current_stock == 97
        
        print(f"Transaction Total: {updated_tx.total_amount}") # Should be 250 - 100 = 150
        assert updated_tx.total_amount == 150.0
        
        # Check Detail Quantity
        detail = updated_tx.details[0]
        assert detail.quantity == 3 # 5 - 2
        
        print("SUCCESS: Void Line Item verified.")

    except Exception:
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_void_item()
