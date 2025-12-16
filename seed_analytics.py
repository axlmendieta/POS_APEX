import random
from datetime import datetime, timedelta
from database import SessionLocal
import crud
from models import Product, Category, Transaction, TransactionDetail, Location

def seed_analytics_data():
    db = SessionLocal()
    try:
        log("Starting Analytics Seeding...")

        # 1. Create Categories
        categories = ["Beverage", "Snack", "Dairy", "Bakery", "Household"]
        cat_objs = {}
        for c_name in categories:
            cat = crud.get_category_by_name(db, c_name)
            if not cat:
                cat = crud.create_category(db, c_name)
            cat_objs[c_name] = cat
        log(f"Ensured {len(categories)} Categories.")

        # 2. Create 50 Products
        # Basic naming templates
        adjectives = ["Organic", "Premium", "Small", "Large", "Family Pack", "Spicy", "Sweet"]
        nouns = {
            "Beverage": ["Juice", "Water", "Soda", "Tea", "Coffee", "Energy Drink", "Milkshake"],
            "Snack": ["Chips", "Nuts", "Pretzels", "Cookies", "Crackers", "Popcorn", "Bar"],
            "Dairy": ["Milk", "Cheese", "Yogurt", "Butter", "Cream", "Custard"],
            "Bakery": ["Bread", "Croissant", "Muffin", "Bagel", "Donut", "Cake"],
            "Household": ["Cleaner", "Tissues", "Soap", "Detergent", "Foil", "Batteries"]
        }

        created_products = []
        
        # 1b. Create Locations
        location_names = ["Main Branch", "Mall Kiosk", "Airport Store"]
        loc_ids = []
        for l_name in location_names:
            loc = db.query(Location).filter(Location.name == l_name).first()
            if not loc:
                loc = Location(name=l_name, location_type="store")
                db.add(loc)
                db.commit()
                db.refresh(loc)
            loc_ids.append(loc.id)
        log(f"Ensured {len(loc_ids)} Locations.")

        # 2. Create 50 Products
        # ... (products code remains) ...
        # Ensure at least one product per category base, then fill up to 50
        for i in range(50):
            cat_name = random.choice(categories)
            name = f"{random.choice(adjectives)} {random.choice(nouns[cat_name])} {random.randint(100,999)}"
            price = round(random.uniform(0.50, 20.00), 2)
            
            # Check existence
            existing = db.query(Product).filter(Product.name == name).first()
            if not existing:
                p = Product(name=name, price=price, category_id=cat_objs[cat_name].id)
                db.add(p)
                db.commit()
                db.refresh(p)
                created_products.append(p)
                # Init Stock for ALL locations
                for lid in loc_ids:
                    crud.update_stock(db, lid, p.id, random.randint(10, 200))
            else:
                created_products.append(existing)

        log(f"Ensured 50+ Products.")

        # 3. Create 100+ Transactions over last 30 days
        
        for i in range(150): # Increased to 150 for better spread
            # Random date in last 30 days
            days_ago = random.randint(0, 30)
            tx_date = datetime.utcnow() - timedelta(days=days_ago)
            
            # Random Location
            loc_id = random.choice(loc_ids)

            # Create Transaction
            tx = Transaction(
                total_amount=0, # Will calc
                status="completed",
                created_at=tx_date,
                selling_location_id=loc_id,
                employee_id=1 # Default admin
            )
            db.add(tx)
            db.commit()
            db.refresh(tx)
            
            # Add Details (1-8 items)
            total = 0.0
            num_items = random.randint(1, 8)
            for _ in range(num_items):
                prod = random.choice(created_products)
                qty = random.randint(1, 3)
                detail = TransactionDetail(
                    transaction_id=tx.id,
                    product_id=prod.id,
                    quantity=qty,
                    unit_price=prod.price
                )
                db.add(detail)
                total += (float(prod.price) * qty)
            
            tx.total_amount = total
            db.commit()
            
            # Progress log every 20
            if i % 20 == 0:
                log(f"  Generated {i} transactions...")

        log("Seeding Complete. Analytics data ready.")

    except Exception as e:
        log(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

# Logger
def log(msg):
    with open("debug_seed.txt", "a") as f:
        f.write(msg + "\n")
    print(msg)

if __name__ == "__main__":
    # Clear log
    with open("debug_seed.txt", "w") as f:
        f.write("Starting Log...\n")
        
    log("Running seed_analytics_data...")
    try:
        seed_analytics_data()
        log("FINISHED SUCCESS.")
    except Exception as e:
        log(f"CRITICAL ERROR: {e}")
        import traceback
        log(traceback.format_exc())
