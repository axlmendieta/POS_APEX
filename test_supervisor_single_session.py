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

def test_logic():
    setup_db()
    db = SessionLocal()
    try:
        # Setup Data
        warehouse = crud.create_location(db, "HQ Warehouse", "warehouse")
        store_A = crud.create_location(db, "Store A", "store")
        store_B = crud.create_location(db, "Store B", "store")
        
        super_admin = crud.create_employee(db, "admin_user", "super_admin", "pwd", warehouse.id)
        manager_A = crud.create_employee(db, "manager_a", "branch_manager", "pwd", store_A.id)
        cashier_A = crud.create_employee(db, "cashier_a", "internal_cashier", "pwd", store_A.id)
        manager_B = crud.create_employee(db, "manager_b", "branch_manager", "pwd", store_B.id)

        prod = crud.create_product(db, "Void Item", 50.0)
        # Initial Stock: 100
        crud.update_stock(db, store_A.id, prod.id, 100) 
        
        db.commit() # Commit setup data
        
        # --- Create Sale ---
        print("Creating Sale...")
        items = [{'product_id': prod.id, 'quantity': 5, 'unit_price': 50.0}]
        tx = service_logic.process_sale(db, store_A.id, cashier_A.id, items)
        tx_id = tx.id
        
        # Verify Stock Decrement
        db.refresh(prod) # Refresh product/stock rels?
        stock = crud.get_stock_level(db, store_A.id, prod.id)
        db.refresh(stock)
        print(f"Stock after sale: {stock.current_stock}")
        assert stock.current_stock == 95

        # --- Scenario 1: Cashier Void (Fail) ---
        print("\nScenario 1: Cashier Void (Expect Fail)...")
        try:
            service_logic.cancel_transaction(db, tx_id, cashier_A.id)
            print("FAILED: Cashier was NOT blocked.")
        except PermissionError:
            print("SUCCESS: Cashier blocked.")
            db.rollback() # Reset validation failure

        # --- Scenario 2: Wrong Manager Void (Fail) ---
        print("\nScenario 2: Wrong Manager Void (Expect Fail)...")
        try:
            service_logic.cancel_transaction(db, tx_id, manager_B.id)
            print("FAILED: Wrong Manager was NOT blocked.")
        except PermissionError:
            print("SUCCESS: Wrong Manager blocked.")
            db.rollback()

        # --- Scenario 3: Correct Manager Void (Success) ---
        print("\nScenario 3: Correct Manager Void (Expect Success)...")
        # Need to re-fetch tx_id because rollback might have detached it? 
        # Actually rollback undoes everything since last commit.
        # The 'sale' was committed in process_sale. So rollback reverts to state AFTER sale.
        
        cancelled_tx = service_logic.cancel_transaction(db, tx_id, manager_A.id)
        assert cancelled_tx.status == 'cancelled'
        
        db.refresh(stock)
        print(f"Stock after void: {stock.current_stock}")
        assert stock.current_stock == 100
        print("SUCCESS: Stock Reversed.")

        # --- Scenario 4: Delete Product ---
        print("\nScenario 4: Delete Product...")
        
        # Manager Fail
        try:
            service_logic.delete_product_secure(db, prod.id, manager_A.id)
        except PermissionError:
            print("SUCCESS: Manager blocked.")
            db.rollback()
            
        # Admin Success
        res = service_logic.delete_product_secure(db, prod.id, super_admin.id)
        assert res is True
        
        check = crud.get_product(db, prod.id)
        assert check is None
        print("SUCCESS: Product Deleted.")

    except Exception:
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_logic()
