from sqlalchemy.orm import Session
from sqlalchemy import func, desc, text
from models import Product, Category, Location, StockLevel, Customer, Transaction, TransactionDetail, Employee, StockTransfer
from datetime import datetime, timedelta, date

# --- Categories ---
def create_category(db: Session, name: str):
    db_category = Category(name=name)
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def get_category_by_name(db: Session, name: str):
    return db.query(Category).filter(Category.name == name).first()

# --- Products ---
def create_product(db: Session, name: str, price: float, category_id: int = None, barcode: str = None, cost_price: float = None, wholesale_price: float = None):
    db_product = Product(
        name=name,
        price=price,
        category_id=category_id,
        barcode=barcode,
        cost_price=cost_price,
        wholesale_price=wholesale_price
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def get_product(db: Session, product_id: int):
    return db.query(Product).filter(Product.id == product_id).first()

def get_product_by_barcode(db: Session, barcode: str):
    return db.query(Product).filter(Product.barcode == barcode).first()

# --- Locations ---
def create_location(db: Session, name: str, location_type: str, address: str = None, tax_id: str = None, contact_info: str = None):
    db_location = Location(name=name, location_type=location_type, address=address, tax_id=tax_id, contact_info=contact_info)
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

def get_location(db: Session, location_id: int):
    return db.query(Location).filter(Location.id == location_id).first()

# --- Employees ---
def create_employee(db: Session, username: str, role: str, password_hash: str, location_id: int = None):
    db_employee = Employee(
        username=username, 
        role=role, 
        password_hash=password_hash, 
        assigned_location_id=location_id
    )
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee

def get_employee_by_username(db: Session, username: str):
    return db.query(Employee).filter(Employee.username == username).first()

# --- Customers ---
def create_customer(db: Session, name: str, email: str = None, phone: str = None):
    db_customer = Customer(name=name, email=email, phone=phone)
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

def update_customer_metrics(db: Session, customer_id: int, purchase_amount: float, purchase_date: datetime):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if customer:
        customer.last_purchase_date = purchase_date
        customer.last_purchase_amount = purchase_amount
        # Note: logic for updating favorite product would be more complex (aggregation), skipped for simple CRUD
        db.commit()
        db.refresh(customer)
    return customer

# --- Stock ---
def get_stock_level(db: Session, location_id: int, product_id: int):
    return db.query(StockLevel).filter(
        StockLevel.location_id == location_id,
        StockLevel.product_id == product_id
    ).first()

def update_stock(db: Session, location_id: int, product_id: int, quantity_change: int, commit: bool = True):
    """
    Updates stock level. quantity_change can be positive (add) or negative (subtract).
    Creates StockLevel record if it doesn't exist.
    """
    stock = get_stock_level(db, location_id, product_id)

    if not stock:
        # Create new record if creating stock checks normally implies existence, 
        # but here we allow auto-creation for initialization
        stock = StockLevel(location_id=location_id, product_id=product_id, current_stock=0)
        db.add(stock)
    
    # Calculate new stock level
    new_stock = stock.current_stock + quantity_change
    
    # Enforce Stock Integrity
    if new_stock < 0:
        raise ValueError(f"Insufficient stock for product {product_id} at location {location_id}. Current: {stock.current_stock}, Requested Change: {quantity_change}")

    stock.current_stock = new_stock
    
    if commit:
        db.commit()
        db.refresh(stock)
    return stock

# --- Transactions (Complex) ---
def create_transaction_with_details(
    db: Session, 
    selling_location_id: int,
    employee_id: int,
    items: list[dict], # [{'product_id': 1, 'quantity': 2, 'unit_price': 10.0}]
    customer_id: int = None,
    commit: bool = True
):
    """
    Creates a transaction and its details atomically.
    Does NOT decrement stock (business logic usually separates this or wraps it).
    For this CRUD, we just save the record.
    """
    total_amount = sum(item['quantity'] * item['unit_price'] for item in items)
    
    # 1. Create Header
    transaction = Transaction(
        selling_location_id=selling_location_id,
        employee_id=employee_id,
        customer_id=customer_id,
        total_amount=total_amount
    )
    db.add(transaction)
    db.flush() # Flush to get transaction.id

    # 2. Create Details
    for item in items:
        # Get product cost for margin analysis (simplified: current cost)
        product = get_product(db, item['product_id'])
        current_cost = product.cost_price if product.cost_price else 0
        
        detail = TransactionDetail(
            transaction_id=transaction.id,
            product_id=item['product_id'],
            quantity=item['quantity'],
            unit_price=item['unit_price'],
            unit_cost_at_sale=current_cost
        )
        db.add(detail)
    
    if commit:
        db.commit()
        db.refresh(transaction)
    return transaction

def create_stock_transfer(
    db: Session, 
    product_id: int, 
    source_location_id: int, 
    destination_location_id: int, 
    quantity_moved: int, 
    employee_id: int, 
    status: str = 'completed'
):
    """
    Atomically moves stock from source to destination.
    1. Decrement Source (commit=False)
    2. Increment Destination (commit=False)
    3. Create Transfer Record
    4. Commit
    """
    # 1. Decrement Source
    update_stock(db, source_location_id, product_id, -quantity_moved, commit=False)
    
    # 2. Increment Destination
    update_stock(db, destination_location_id, product_id, quantity_moved, commit=False)
    
    # 3. Create Transfer Record
    transfer = StockTransfer(
        source_location_id=source_location_id,
        destination_location_id=destination_location_id,
        product_id=product_id,
        quantity_moved=quantity_moved,
        employee_id=employee_id,
        status=status,
        transfer_date=datetime.now() # Depending on model default, but safe to set
    )
    db.add(transfer)
    
    # 4. Commit Atomically
    db.commit()
    db.refresh(transfer)
    return transfer

# --- Safety/Admin Support ---
def delete_product(db: Session, product_id: int):
    """
    Deletes a product. Should be guarded by service layer validation.
    """
    product = get_product(db, product_id)
    if product:
        db.delete(product)
        db.commit()
        return True
    return False

def get_transaction(db: Session, transaction_id: int):
    return db.query(Transaction).filter(Transaction.id == transaction_id).first()

def update_transaction_status(db: Session, transaction_id: int, status: str):
    transaction = get_transaction(db, transaction_id)
    if transaction:
        transaction.status = status
        db.commit()
        db.refresh(transaction)
    return transaction

def get_employee(db: Session, employee_id: int):
    return db.query(Employee).filter(Employee.id == employee_id).first()

# --- Reporting ---
def get_daily_sales_stats(db: Session, location_id: int):
    """
    Returns total revenue and transaction count for today.
    Simplicity: Ignores timezone (uses server/db local time logic for 'today').
    """
    today = datetime.now().date()
    stats = db.query(
        func.sum(Transaction.total_amount).label('total_revenue'),
        func.count(Transaction.id).label('tx_count')
    ).filter(
        Transaction.selling_location_id == location_id,
        Transaction.status == 'completed',
        func.date(Transaction.created_at) == today
    ).first()
    
    return {
        "total_revenue": stats.total_revenue or 0.0,
        "tx_count": stats.tx_count or 0
    }

def get_recent_transactions(db: Session, location_id: int, limit: int = 5):
    """
    Returns the last N transactions for the location.
    """
    return db.query(Transaction).filter(
        Transaction.selling_location_id == location_id,
        Transaction.status == 'completed'
    ).order_by(Transaction.created_at.desc()).limit(limit).all()

# --- Analytics ---
def get_sales_over_time(db: Session, location_id: int, days: int = 7):
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # SQLite/Postgres difference in date truncation usually requires careful handling.
    # We will cast created_at to Date for grouping.
    results = db.query(
        func.date(Transaction.created_at).label('date'),
        func.sum(Transaction.total_amount).label('total_revenue'),
        func.count(Transaction.id).label('tx_count')
    ).filter(
        Transaction.created_at >= start_date,
        Transaction.location_id == location_id
    ).group_by(
        func.date(Transaction.created_at)
    ).order_by(
        func.date(Transaction.created_at)
    ).all()
    
    return [
        {"date": str(r.date), "revenue": float(r.total_revenue or 0), "count": r.tx_count}
        for r in results
    ]

def get_top_products(db: Session, location_id: int, limit: int = 10):
    results = db.query(
        Product.name,
        func.sum(TransactionDetail.quantity).label('total_qty')
    ).join(
        TransactionDetail, Product.id == TransactionDetail.product_id
    ).join(
        Transaction, TransactionDetail.transaction_id == Transaction.id
    ).filter(
        Transaction.location_id == location_id
    ).group_by(
        Product.id
    ).order_by(
        desc('total_qty')
    ).limit(limit).all()
    
    return [
        {"name": r.name, "quantity": r.total_qty}
        for r in results
    ]

def get_dashboard_kpis(db: Session, location_id: int):
    # For simplicity, getting "Lifetime" stats or "Today's" stats? 
    # Let's do Today vs Total to be useful.
    
    today = datetime.utcnow().date()
    
    # 1. Total Revenue (Today)
    revenue_today = db.query(func.sum(Transaction.total_amount)).filter(
        Transaction.location_id == location_id,
        func.date(Transaction.created_at) == today
    ).scalar() or 0.0

    # 2. Tx Count (Today)
    count_today = db.query(func.count(Transaction.id)).filter(
        Transaction.location_id == location_id,
        func.date(Transaction.created_at) == today
    ).scalar() or 0

    # 3. Avg Ticket (Today)
    avg_ticket = revenue_today / count_today if count_today > 0 else 0.0

    return {
        "revenue_today": float(revenue_today),
        "count_today": count_today,
        "avg_ticket": float(avg_ticket)
    }

def get_sales_by_category(db: Session, location_id: int):
    results = db.query(
        Category.name,
        func.sum(TransactionDetail.quantity).label('total_qty')
    ).join(
        Product, Category.id == Product.category_id
    ).join(
        TransactionDetail, Product.id == TransactionDetail.product_id
    ).join(
        Transaction, TransactionDetail.transaction_id == Transaction.id
    ).filter(
        Transaction.location_id == location_id
    ).group_by(
        Category.id
    ).all()

    return [
        {"name": r.name, "value": r.total_qty}
        for r in results
    ]

# --- Inventory ---
def get_inventory_levels(db: Session, location_id: int):
    results = db.query(
        Product.id, 
        Product.name, 
        Category.name.label('category'), 
        StockLevel.current_stock
    ).join(
        StockLevel, Product.id == StockLevel.product_id
    ).join(
        Category, Product.category_id == Category.id
    ).filter(
        StockLevel.location_id == location_id
    ).all()
    
    return [
        {"id": r.id, "name": r.name, "category": r.category, "stock": r.current_stock}
        for r in results
    ]

def get_revenue_by_location(db: Session):
    results = db.query(
        Location.name,
        func.sum(Transaction.total_amount).label('revenue')
    ).join(
        Transaction, Location.id == Transaction.selling_location_id
    ).group_by(
        Location.id
    ).all()

    return [
        {"location": r.name, "revenue": float(r.revenue)}
        for r in results
    ]

def get_revenue_by_location(db: Session):
    results = db.query(
        Location.name,
        func.sum(Transaction.total_amount).label('revenue')
    ).join(
        Transaction, Location.id == Transaction.selling_location_id
    ).group_by(
        Location.id
    ).all()

    return [
        {"location": r.name, "revenue": float(r.revenue)}
        for r in results
    ]
