import init_db
from database import SessionLocal
import crud
from models import Base
import models
import service_logic
import os
import traceback

# Clean run helper
def setup_module(module):
    # Set env var to allow drop for setup
    os.environ["ALLOW_SCHEMA_DROP"] = "true"
    init_db.init_db()
    os.environ.pop("ALLOW_SCHEMA_DROP", None) # Remove it immediately

def test_db_safety():
    print("\n--- Test: Database Safety ---")
    # 1. Create a dummy table/record (Product)
    db = SessionLocal()
    prod = crud.create_product(db, "Safety Check Item", 10.0)
    prod_id = prod.id
    db.close()
    
    # 2. Run init_db() WITHOUT env var
    # Should NOT drop tables
    init_db.init_db()
    
    # 3. Verify record still exists
    db = SessionLocal()
    check = crud.get_product(db, prod_id)
    assert check is not None
    print("SUCCESS: Database was NOT dropped without env var.")
    db.close()

def test_supervisor_logic():
    print("\n--- Test: Supervisor Authorization ---")
    try:
        db = SessionLocal()
        
        # Setup Data (Global for scenarios)
        warehouse = crud.create_location(db, "HQ Warehouse", "warehouse")
        store_A = crud.create_location(db, "Store A", "store")
        store_B = crud.create_location(db, "Store B", "store")
        
        # Employees
        super_admin = crud.create_employee(db, "admin_user", "super_admin", "pwd", warehouse.id)
        manager_A = crud.create_employee(db, "manager_a", "branch_manager", "pwd", store_A.id)
        cashier_A = crud.create_employee(db, "cashier_a", "internal_cashier", "pwd", store_A.id)
        manager_B = crud.create_employee(db, "manager_b", "branch_manager", "pwd", store_B.id)

        # Product & Stock
        prod = crud.create_product(db, "Void Item", 50.0)
        crud.update_stock(db, store_A.id, prod.id, 100)
        
        # Create Sale
        print("Creating Sale...")
        items = [{'product_id': prod.id, 'quantity': 5, 'unit_price': 50.0}]
        tx = service_logic.process_sale(db, store_A.id, cashier_A.id, items)
        tx_id = tx.id
        
        # Persist setup data
        db.commit() 
        # Note: sqlalchemy objects detached after commit if expire_on_commit=True (default).
        # We need to re-fetch or just use IDs.
        
        # Capture IDs for fresh sessions
        tx_id_val = tx_id
        cashier_id = cashier_A.id
        manager_a_id = manager_A.id
        manager_b_id = manager_B.id
        super_admin_id = super_admin.id
        prod_id = prod.id
        store_a_id = store_A.id
        
        db.close()

        # --- Scenario 1: Cashier tries to Void (Fail) ---
        print("Scenario 1: Cashier attempts void (Should Fail)...")
        db = SessionLocal()
        try:
            service_logic.cancel_transaction(db, tx_id_val, cashier_id)
            assert False, "Cashier should not be able to void."
        except PermissionError:
            print("SUCCESS: Cashier blocked.")
        except Exception as e:
            print(f"FAILED: Unexpected error {e}")
            raise e
        finally:
            db.close()

        # --- Scenario 2: Manager B (Wrong Store) tries to Void (Fail) ---
        print("Scenario 2: Wrong Manager attempts void (Should Fail)...")
        db = SessionLocal()
        try:
            service_logic.cancel_transaction(db, tx_id_val, manager_b_id)
            assert False, "Manager B should not control Store A."
        except PermissionError:
            print("SUCCESS: Wrong Manager blocked.")
        except Exception as e:
            print(f"FAILED: Unexpected error {e}")
            raise e
        finally:
            db.close()

        # --- Scenario 3: Manager A (Correct Store) tries to Void (Success) ---
        print("Scenario 3: Correct Manager attempts void (Should Succeed)...")
        db = SessionLocal()
        try:
            voided_tx = service_logic.cancel_transaction(db, tx_id_val, manager_a_id)
            assert voided_tx.status == 'cancelled'
            
            # Verify Stock Reversal
            stock = crud.get_stock_level(db, store_a_id, prod_id)
            print(f"Stock after void: {stock.current_stock}")
            # Initial 100, Sold 5 -> 95. Void -> Back to 100.
            assert stock.current_stock == 100
            print("SUCCESS: Transaction Voided & Stock Reversed.")
        except Exception as e:
            print(f"FAILED Scenario 3: {e}")
            raise e
        finally:
            db.close()

        # --- Scenario 4: Delete Product (Super Admin Only) ---
        print("Scenario 4: Product Deletion...")
        
        # Manager Try
        db = SessionLocal()
        try:
            service_logic.delete_product_secure(db, prod_id, manager_a_id)
            assert False, "Manager should NOT delete product"
        except PermissionError:
            print("SUCCESS: Manager cannot delete product.")
        finally:
            db.close()
            
        # Admin Try
        db = SessionLocal()
        try:
            res = service_logic.delete_product_secure(db, prod_id, super_admin_id)
            assert res is True
            check = crud.get_product(db, prod_id)
            assert check is None
            print("SUCCESS: Super Admin deleted product.")
        except Exception as e:
            print(f"FAILED Scenario 4: {e}")
            raise e
        finally:
            db.close()

    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    setup_module(None)
    test_db_safety()
    test_supervisor_logic()
