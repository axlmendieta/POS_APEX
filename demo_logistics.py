from database import SessionLocal
from init_db import init_db
import crud

def demo_logistics():
    # 1. Setup & Reset
    print("\n--- Logistics Demo: Setup ---")
    init_db()
    db = SessionLocal()
    
    try:
        # Create Locations
        warehouse = crud.create_location(db, "Central Warehouse", "warehouse")
        store = crud.create_location(db, "Downtown Store", "store")
        print(f"Locations Created: {warehouse.name}, {store.name}")
        
        # Create Product
        prod = crud.create_product(db, "Logistics Item", 50.00)
        print(f"Product Created: {prod.name}")
        
        # Create Employee (for audit)
        emp = crud.create_employee(db, "logistics_manager", "logistics", "hash", warehouse.id)
        
        # 2. Initial Stock
        print("\n--- Initializing Stock ---")
        # Initialize Warehouse with 100
        crud.update_stock(db, warehouse.id, prod.id, 100)
        # Store starts with 0 (implicit)
        
        wh_stock = crud.get_stock_level(db, warehouse.id, prod.id)
        print(f"Warehouse Stock: {wh_stock.current_stock}")
        assert wh_stock.current_stock == 100

        # 3. Execute Transfer
        print("\n--- Executing Stock Transfer (30 Units) ---")
        transfer = crud.create_stock_transfer(
            db, 
            product_id=prod.id, 
            source_location_id=warehouse.id, 
            destination_location_id=store.id, 
            quantity_moved=30, 
            employee_id=emp.id
        )
        print(f"Transfer Recorded: ID {transfer.id}, Status: {transfer.status}")

        # 4. Verification
        print("\n--- Verifying Final Stock Levels ---")
        # Refresh or fetch new stock levels
        # (Need to fetch store stock first time likely)
        
        wh_stock_final = crud.get_stock_level(db, warehouse.id, prod.id)
        store_stock_final = crud.get_stock_level(db, store.id, prod.id)
        
        print(f"Warehouse Stock: {wh_stock_final.current_stock} (Expected 70)")
        print(f"Store Stock: {store_stock_final.current_stock} (Expected 30)")
        
        assert wh_stock_final.current_stock == 70
        assert store_stock_final.current_stock == 30
        
        print("\nLOGISTICS DEMO COMPLETED SUCCESSFULLY!")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"DEMO FAILED: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    demo_logistics()
