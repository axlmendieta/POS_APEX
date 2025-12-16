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

def test_simple():
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
        
        # Create Sale
        print("Creating Sale...")
        items = [{'product_id': prod.id, 'quantity': 5, 'unit_price': 50.0}]
        tx = service_logic.process_sale(db, store_A.id, cashier_A.id, items)
        tx_id = tx.id
        
        # Verify Stock Decrement
        stock = crud.get_stock_level(db, store_A.id, prod.id)
        print(f"Stock after sale: {stock.current_stock}")
        assert stock.current_stock == 95

        # Void (Success)
        print("Voiding Transaction...")
        cancelled_tx = service_logic.cancel_transaction(db, tx_id, manager_A.id)
        assert cancelled_tx.status == 'cancelled'
        
        db.refresh(stock)
        print(f"Stock after void: {stock.current_stock}")
        assert stock.current_stock == 100
        print("SUCCESS")

    except Exception:
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_simple()
