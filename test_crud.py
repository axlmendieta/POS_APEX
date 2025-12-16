from database import SessionLocal
from init_db import init_db
import crud
from datetime import datetime

def test_crud_operations():
    # 1. Reset DB
    print("Initializing Database...")
    init_db()
    
    db = SessionLocal()
    try:
        print("\n--- Testing Products & Categories ---")
        cat = crud.create_category(db, name="Electronics")
        print(f"Created Category: {cat.name}")
        
        prod = crud.create_product(db, name="Laptop", price=999.99, category_id=cat.id, cost_price=800.00)
        print(f"Created Product: {prod.name}, Price: {prod.price}")
        
        fetched_prod = crud.get_product(db, prod.id)
        assert fetched_prod.name == "Laptop"
        print("Product retrieval verified.")

        print("\n--- Testing Locations & Stock ---")
        loc = crud.create_location(db, name="Main Warehouse", location_type="warehouse")
        print(f"Created Location: {loc.name}")
        
        # Initial Stock
        stock = crud.update_stock(db, loc.id, prod.id, 50)
        print(f"Stock Initialized: {stock.current_stock}")
        assert stock.current_stock == 50
        
        # Add Stock
        stock = crud.update_stock(db, loc.id, prod.id, 10)
        print(f"Stock Updated: {stock.current_stock}")
        assert stock.current_stock == 60

        print("\n--- Testing Employees & Customers ---")
        emp = crud.create_employee(db, "manager", "admin", "hash123", loc.id)
        cust = crud.create_customer(db, "Alice Smith")
        print(f"Created Employee: {emp.username}")
        print(f"Created Customer: {cust.name}")

        print("\n--- Testing Transactions ---")
        items = [
            {'product_id': prod.id, 'quantity': 2, 'unit_price': 999.99}
        ]
        trans = crud.create_transaction_with_details(
            db, 
            selling_location_id=loc.id, 
            employee_id=emp.id, 
            items=items, 
            customer_id=cust.id
        )
        print(f"Transaction Created with Total: {trans.total_amount}")
        assert len(trans.details) == 1
        assert float(trans.total_amount) == 1999.98
        
        # Test Metrics Update
        cust = crud.update_customer_metrics(db, cust.id, float(trans.total_amount), trans.created_at)
        print(f"Customer Metrics Updated: Last Purchase {cust.last_purchase_amount}")
        assert float(cust.last_purchase_amount) == 1999.98

        print("\nALL CRUD TESTS PASSED SUCCESSFULLY!")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"TEST FAILED: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_crud_operations()
