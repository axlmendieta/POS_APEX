from database import SessionLocal
import crud
from models import Location, Transaction
from sqlalchemy import func

def debug_locs():
    db = SessionLocal()
    try:
        print("--- Locations ---")
        locs = db.query(Location).all()
        for l in locs:
            print(f"ID: {l.id}, Name: {l.name}")
        
        print("\n--- Sales per Location ---")
        sales = db.query(
            Transaction.selling_location_id, 
            func.count(Transaction.id),
            func.sum(Transaction.total_amount)
        ).group_by(Transaction.selling_location_id).all()
        
        for loc_id, count, total in sales:
            print(f"Loc ID {loc_id}: {count} txs, ${total}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_locs()
