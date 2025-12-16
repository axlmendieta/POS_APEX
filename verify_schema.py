from database import SessionLocal, engine
from models import Base, Location, Product, StockLevel, StockTransfer, Transaction, TransactionDetail, Category, Employee, Customer
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from init_db import init_db
import datetime

def verify_schema():
    # Reset DB
    init_db()
    
    session = SessionLocal()
    try:
        print("Checking tables...")
        # Check if tables exist
        inspector = text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = session.execute(inspector).fetchall()
        print("Tables found:", [t[0] for t in tables])

        # 1. Create Data
        print("\nCreating test data...")
        
        # Location
        wh = Location(name="Central Warehouse", location_type="warehouse", address="123 Main St")
        store = Location(name="Retail Store 1", location_type="store", address="456 Market St")
        partner = Location(name="Partner Store A", location_type="partner", address="789 Partner Rd")
        session.add_all([wh, store, partner])
        session.flush()

        # Category & Product
        cat = Category(name="Beverages")
        session.add(cat)
        session.flush()

        prod = Product(name="Soda Can", category_id=cat.id, barcode="123456789", price=15.50, cost_price=10.00)
        session.add(prod)
        session.flush()

        # Stock Level
        stock = StockLevel(location_id=wh.id, product_id=prod.id, current_stock=100, reorder_point=20)
        session.add(stock)
        
        # Employee
        emp = Employee(username="admin_user", role="admin", password_hash="hashed_secret")
        session.add(emp)
        session.flush()

        # Stock Transfer
        transfer = StockTransfer(
            source_location_id=wh.id, 
            destination_location_id=store.id, 
            product_id=prod.id, 
            quantity_moved=50, 
            employee_id=emp.id,
            status="completed"
        )
        session.add(transfer)

        # Transaction
        # Correct Customer creation
        cust = Customer(
            name="Jane Doe", 
            loyalty_points=10, 
            last_purchase_amount=150.00, 
            favorite_product_id=prod.id
        )
        session.add(cust)
        session.flush()

        # Test Bidirectional Relationship
        print(f"Customer favorite product: {cust.favorite_product.name}")
        assert cust in prod.favorited_by_customers
        print("Bidirectional relationship verified: Customer found in Product.favorited_by_customers")

        trans = Transaction(
            selling_location_id=store.id,
            employee_id=emp.id,
            customer_id=cust.id,
            total_amount=31.00
        )
        session.add(trans)
        session.flush()

        # Transaction Detail (Testing unit_cost_at_sale)
        detail = TransactionDetail(
            transaction_id=trans.id,
            product_id=prod.id,
            quantity=2,
            unit_price=15.50,
            unit_cost_at_sale=10.00
        )
        session.add(detail)

        session.commit()
        print("Data inserted successfully!")

        # 2. Test Constraints
        print("\nTesting Constraints...")
        
        # Test Invalid Location Type
        try:
            bad_loc = Location(name="Bad Loc", location_type="invalid_type")
            session.add(bad_loc)
            session.commit()
            print("ERROR: Invalid location_type check failed!")
        except IntegrityError:
            print("SUCCESS: Invalid location_type caught.")
            session.rollback()

        # Test Negative Price
        try:
            bad_prod = Product(name="Bad Price", price=-5.00)
            session.add(bad_prod)
            session.commit()
            print("ERROR: Negative price check failed!")
        except IntegrityError:
            print("SUCCESS: Negative price caught.")
            session.rollback()

        # Test Negative Purchase Amount
        try:
            bad_cust = Customer(name="Bad Cust", last_purchase_amount=-10.00)
            session.add(bad_cust)
            session.commit()
            print("ERROR: Negative purchase amount check failed!")
        except IntegrityError:
            print("SUCCESS: Negative purchase amount caught.")
            session.rollback()

    except Exception as e:
        print(f"Verification failed: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    verify_schema()
