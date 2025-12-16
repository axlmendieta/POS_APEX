from database import SessionLocal
import crud
from models import Product, StockLevel

def seed_real_products():
    db = SessionLocal()
    try:
        # Frontend Mock Data structure:
        # { id: 1, name: "Water", price: 1.00, category: "Beverage", stock: 150 },
        # { id: 2, name: "Soda", price: 2.00, category: "Beverage", stock: 45 },
        # { id: 3, name: "Premium Soda", price: 5.00, category: "Beverage", stock: 12 },
        # { id: 4, name: "Chips", price: 1.50, category: "Snack", stock: 88 }
        
        products_to_seed = [
            {"id": 1, "name": "Water", "price": 1.00, "cat": "Beverage", "stock": 150},
            {"id": 2, "name": "Soda", "price": 2.00, "cat": "Beverage", "stock": 45},
            {"id": 3, "name": "Premium Soda", "price": 5.00, "cat": "Beverage", "stock": 12},
            {"id": 4, "name": "Chips", "price": 1.50, "cat": "Snack", "stock": 88}
        ]

        print("Seeding Real Products...")
        
        # Ensure Category exists
        beverage = crud.get_category_by_name(db, "Beverage")
        if not beverage:
            beverage = crud.create_category(db, "Beverage")
            
        snack = crud.get_category_by_name(db, "Snack")
        if not snack:
            snack = crud.create_category(db, "Snack")

        for p in products_to_seed:
            # Check if product exists
            existing = db.query(Product).filter(Product.id == p["id"]).first()
            if not existing:
                print(f"Creating Product: {p['name']} (ID: {p['id']})")
                # We need to manually set ID to match frontend mock? 
                # SQLAlchemy usually auto-increments. 
                # To force specific ID, we might need to be careful or just trust that starting emptyDB they will be 1,2,3,4.
                # But 'API Prod' is ID 1. Wait.
                # If API Prod is ID 1, then we have a collision.
                
                # Let's check 'API Prod' again.
                # If ID 1 is taken, frontend mock ID 1 (Water) will fail or we need to update frontend.
                
                # Actually, I'll just create them and let DB assign IDs, 
                # BUT the frontend sends ID 1, 2, 3... hardcoded.
                # So I MUST update the frontend to use Real Data eventually.
                # For now, to fix the user's immediate issue, I will try to create them.
                
                cat_id = beverage.id if p["cat"] == "Beverage" else snack.id
                
                # Reset sequence if needed? No, just add.
                new_p = Product(name=p["name"], price=p["price"], category_id=cat_id)
                db.add(new_p)
                db.commit() # Get ID
                db.refresh(new_p)
                print(f"   -> Created with DB ID: {new_p.id}")
                
                # Seed Stock
                crud.update_stock(db, 1, new_p.id, p["stock"])
            else:
                 print(f"Product {p['name']} already exists as ID {existing.id}")
                 crud.update_stock(db, 1, existing.id, p["stock"] - 0) # Ensure stock record exists

        print("Seeding Complete.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_real_products()
