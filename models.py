from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Numeric, Text, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

# --- Logistics/Stock ---

class Location(Base):
    __tablename__ = 'locations'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    location_type = Column(String(20), nullable=False) # warehouse, store, partner
    address = Column(Text, nullable=True)
    tax_id = Column(String(50), nullable=True)
    contact_info = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("location_type IN ('warehouse', 'store', 'partner')", name='check_location_type'),
    )

    stock_levels = relationship("StockLevel", back_populates="location")
    sent_transfers = relationship("StockTransfer", foreign_keys="StockTransfer.source_location_id", back_populates="source_location")
    received_transfers = relationship("StockTransfer", foreign_keys="StockTransfer.destination_location_id", back_populates="destination_location")
    transactions = relationship("Transaction", back_populates="selling_location")
    employees = relationship("Employee", back_populates="assigned_location")


class StockLevel(Base):
    __tablename__ = 'stock_levels'

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    current_stock = Column(Integer, default=0, nullable=False)
    reorder_point = Column(Integer, default=10, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint('location_id', 'product_id', name='uq_location_product'),
        CheckConstraint('reorder_point >= 0', name='check_reorder_point_positive'),
    )

    location = relationship("Location", back_populates="stock_levels")
    product = relationship("Product", back_populates="stock_levels")


class StockTransfer(Base):
    __tablename__ = 'stock_transfers'

    id = Column(Integer, primary_key=True, index=True)
    source_location_id = Column(Integer, ForeignKey('locations.id'), nullable=False)
    destination_location_id = Column(Integer, ForeignKey('locations.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity_moved = Column(Integer, nullable=False)
    transfer_date = Column(DateTime(timezone=True), server_default=func.now())
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    status = Column(String(20), default='completed') # pending, in-transit, completed, cancelled

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'in-transit', 'completed', 'cancelled')", name='check_transfer_status'),
        CheckConstraint('quantity_moved > 0', name='check_transfer_quantity_positive'),
    )

    source_location = relationship("Location", foreign_keys=[source_location_id], back_populates="sent_transfers")
    destination_location = relationship("Location", foreign_keys=[destination_location_id], back_populates="received_transfers")
    product = relationship("Product")
    employee = relationship("Employee")


# --- Inventory/Catalog ---

class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    barcode = Column(String(50), unique=True, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    wholesale_price = Column(Numeric(10, 2), nullable=True) # Price for Partners
    cost_price = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint('price >= 0', name='check_price_positive'),
        CheckConstraint('wholesale_price >= 0', name='check_wholesale_price_positive'),
        CheckConstraint('cost_price >= 0', name='check_cost_price_positive'),
    )

    category = relationship("Category", back_populates="products")
    stock_levels = relationship("StockLevel", back_populates="product")
    transaction_details = relationship("TransactionDetail", back_populates="product")
    favorited_by_customers = relationship("Customer", back_populates="favorite_product")


# --- Sales/POS ---

class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, index=True)
    selling_location_id = Column(Integer, ForeignKey('locations.id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), default='completed')
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint('total_amount >= 0', name='check_total_amount_positive'), # Assuming no negative total sales
    )

    selling_location = relationship("Location", back_populates="transactions")
    customer = relationship("Customer", back_populates="transactions")
    employee = relationship("Employee", back_populates="transactions")
    details = relationship("TransactionDetail", back_populates="transaction", cascade="all, delete-orphan")


class TransactionDetail(Base):
    __tablename__ = 'transaction_details'

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey('transactions.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    unit_cost_at_sale = Column(Numeric(10, 2), nullable=False) # Capture cost at time of sale for margin analysis

    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_transaction_detail_quantity_positive'),
        CheckConstraint('unit_price >= 0', name='check_transaction_detail_price_positive'),
        CheckConstraint('unit_cost_at_sale >= 0', name='check_transaction_detail_cost_positive'),
    )

    transaction = relationship("Transaction", back_populates="details")
    product = relationship("Product", back_populates="transaction_details")


# --- Users/Security ---

class Employee(Base):
    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    role = Column(String(20), nullable=False) # admin, cashier, logistics, partner_admin
    assigned_location_id = Column(Integer, ForeignKey('locations.id'), nullable=True)
    password_hash = Column(String(255), nullable=False) # Should store hashed passwords
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    assigned_location = relationship("Location", back_populates="employees")
    transactions = relationship("Transaction", back_populates="employee")


class Customer(Base):
    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=True)
    email = Column(String(100), unique=True, nullable=True)
    phone = Column(String(20), nullable=True)
    loyalty_points = Column(Integer, default=0)
    
    # Customer Metrics
    last_purchase_date = Column(DateTime(timezone=True), nullable=True)
    last_purchase_amount = Column(Numeric(10, 2), nullable=True)
    favorite_product_id = Column(Integer, ForeignKey('products.id'), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        CheckConstraint('loyalty_points >= 0', name='check_loyalty_points_positive'),
        CheckConstraint('last_purchase_amount >= 0', name='check_last_purchase_amount_positive'),
    )

    transactions = relationship("Transaction", back_populates="customer")
    favorite_product = relationship("Product", back_populates="favorited_by_customers")
