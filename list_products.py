from database import SessionLocal
from models import Product

def list_products():
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        print(f"Total Products: {len(products)}")
        for p in products:
            print(f"ID: {p.id} | Name: {p.name}")
    finally:
        db.close()

if __name__ == "__main__":
    list_products()
