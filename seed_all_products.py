from database import SessionLocal
import crud
from sqlalchemy.orm import Session

def seed_all_stock():
    db = SessionLocal()
    try:
        # Seed Products 1 to 50 with 100 stock each
        print("Seeding stock for Products 1-50...")
        for product_id in range(1, 51):
            crud.update_stock(db, 1, product_id, 100)
            
        print("Stock updated successfully for all products.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_all_stock()
