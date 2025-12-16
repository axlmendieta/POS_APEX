from database import SessionLocal
import crud
from models import Product, StockLevel

def debug_soda():
    db = SessionLocal()
    try:
        print("Searching for 'Soda'...")
        products = db.query(Product).filter(Product.name.ilike("%Soda%")).all()
        
        if not products:
            print("❌ No product found with name like 'Soda'")
            return

        for p in products:
            print(f"FOUND Product ID: {p.id}, Name: {p.name}, Price: {p.price}")
            
            stock = db.query(StockLevel).filter(
                StockLevel.product_id == p.id,
                StockLevel.location_id == 1
            ).first()
            
            if stock:
                print(f"   Stock Level (Loc 1): {stock.quantity_on_hand}")
            else:
                print("   ❌ No Stock Record for Location 1!")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_soda()
