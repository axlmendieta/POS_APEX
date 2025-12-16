from database import SessionLocal
import crud
from sqlalchemy.orm import Session

def seed_stock():
    db = SessionLocal()
    try:
        # Ensure Product 1 (Water) has stock at Location 1
        # We'll just add 500.
        print("Seeding stock for Product 1...")
        crud.update_stock(db, 1, 1, 500)
        print("Stock updated successfully.")
        
        # Verify
        stock = crud.get_stock_level(db, 1, 1)
        print(f"Current Stock for Product 1: {stock.current_stock}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_stock()
