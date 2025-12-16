from sqlalchemy.orm import Session
import crud
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Authorization Logic ---
def validate_manager_override(db: Session, supervisor_id: int, required_location_id: int = None):
    """
    Validates if the user has Manager/Admin privileges.
    Returns True if valid, raises PermissionError otherwise.
    
    Logic:
    1. 'super_admin' -> Access ALL.
    2. 'branch_manager' -> Access ONLY their assigned_location_id.
    3. 'partner_owner' -> Access ONLY their assigned_location_id.
    """
    supervisor = crud.get_employee(db, supervisor_id)
    if not supervisor:
        raise PermissionError("Supervisor not found.")
    
    if supervisor.role == 'super_admin':
        return True
    
    if supervisor.role in ['branch_manager', 'partner_owner']:
        if required_location_id and supervisor.assigned_location_id != required_location_id:
            raise PermissionError("Supervisor does not have authority over this location.")
        return True
        
    raise PermissionError(f"User role '{supervisor.role}' is not authorized for Manager Override.")

# --- Transaction Operations ---
def process_sale(db: Session, selling_location_id: int, employee_id: int, items: list[dict], customer_id: int = None):
    """
    Orchestrates a sale atomically:
    1. Decrements stock for all items (validating availability).
    2. Creates transaction record.
    3. Commits only if EVERYTHING succeeds.
    """
    try:
        # Start Atomic Block
        # 1. Decrement Stock (commit=False to defer persistence)
        for item in items:
            crud.update_stock(db, selling_location_id, item['product_id'], -item['quantity'], commit=False)
            
        # 2. Record Transaction (commit=False internal to function or just flush)
        # Note: crud.create_transaction_with_details handles flush, but we must ensure it doesn't auto-commit if we want full atomicity here.
        # Looking at crud.py, create_transaction_with_details DOES commit by default. 
        # We need to pass commit=False to it if it supports it, or rely on Session transaction management.
        # The prompt specified modifying crud to support commit=False or assuming it supports it.
        # Let's check crud.py again or just pass commit=False if the signature allows (it does, based on previous read).
        transaction = crud.create_transaction_with_details(
            db, 
            selling_location_id, 
            employee_id, 
            items, 
            customer_id,
            commit=False
        )
        
        # 3. Final Atomic Commit
        db.commit()
        db.refresh(transaction)
        
        logger.info(f"Sale processed successfully. Transaction ID: {transaction.id}")
        return transaction

    except ValueError as ve:
        db.rollback()
        logger.warning(f"Sale processing failed (Validation): {ve}")
        raise ve
    except Exception as e:
        db.rollback()
        logger.error(f"Sale processing failed (Unexpected): {e}")
        raise e

def cancel_transaction(db: Session, transaction_id: int, supervisor_id: int):
    """
    Voids a transaction. Requires Manager Override.
    1. Validate Supervisor.
    2. Fetch Transaction.
    3. Reverse Stock (Increment back to selling location).
    4. Update Status to 'cancelled'.
    """
    try:
        transaction = crud.get_transaction(db, transaction_id)
        if not transaction:
            raise ValueError("Transaction not found.")
            
        if transaction.status == 'cancelled':
            raise ValueError("Transaction is already cancelled.")

        # 1. Validate Supervisor (Must cover the selling location)
        validate_manager_override(db, supervisor_id, transaction.selling_location_id)
        
        # 2. Reverse Stock
        for detail in transaction.details:
            crud.update_stock(
                db, 
                transaction.selling_location_id, 
                detail.product_id, 
                detail.quantity, # Add back
                commit=False
            )
            
        # 3. Update Status
        transaction.status = 'cancelled'
        db.commit()
        db.refresh(transaction)
        
        logger.info(f"Transaction {transaction_id} cancelled by Supervisor {supervisor_id}.")
        return transaction
        
    except Exception as e:
        db.rollback()
        logger.error(f"Cancel Transaction failed: {e}")
        raise e

def void_line_item(db: Session, transaction_id: int, product_id: int, quantity_to_void: int, supervisor_id: int):
    """
    voids specific quantity of an item from a transaction.
    1. Validate Supervisor.
    2. Check item exists and has enough quantity.
    3. Reverse Stock (Increment).
    4. Update Transaction Detail (Decrement quantity or remove).
    5. Update Transaction Total.
    """
    try:
        transaction = crud.get_transaction(db, transaction_id)
        if not transaction:
            raise ValueError("Transaction not found.")
        if transaction.status == 'cancelled':
            raise ValueError("Cannot void item from cancelled transaction.")
            
        # 1. Validate Supervisor
        validate_manager_override(db, supervisor_id, transaction.selling_location_id)
        
        # 2. Find Detail
        detail = next((d for d in transaction.details if d.product_id == product_id), None)
        if not detail:
            raise ValueError("Product not found in this transaction.")
        
        if detail.quantity < quantity_to_void:
            raise ValueError(f"Cannot void {quantity_to_void}, only {detail.quantity} in transaction.")
            
        # 3. Reverse Stock (Add back to shelf)
        crud.update_stock(
            db, 
            transaction.selling_location_id, 
            product_id, 
            quantity_to_void, 
            commit=False
        )
        
        # 4. Update Detail & Total
        refund_amount = quantity_to_void * detail.unit_price
        
        if detail.quantity == quantity_to_void:
            db.delete(detail) # Remove line entirely
        else:
            detail.quantity -= quantity_to_void
            
        transaction.total_amount -= refund_amount
        
        db.commit()
        db.refresh(transaction)
        logger.info(f"Voided {quantity_to_void} of Product {product_id} in Transaction {transaction_id}.")
        return transaction

    except Exception as e:
        db.rollback()
        logger.error(f"Void Line Item failed: {e}")
        raise e

# --- Product Operations ---
def delete_product_secure(db: Session, product_id: int, supervisor_id: int):
    """
    Deletes a product. Requires GLOBAL Admin privileges (super_admin).
    """
    try:
        supervisor = crud.get_employee(db, supervisor_id)
        if not supervisor or supervisor.role != 'super_admin':
            raise PermissionError("Only Super Admin can delete products.")
            
        success = crud.delete_product(db, product_id)
        db.commit()
        return True
    
    except Exception as e:
        logger.error(f"Delete Product failed: {e}")
        raise e

# --- Polymorphic Multi-Tenant Logic ---

def create_wholesale_order(db: Session, source_location_id: int, partner_location_id: int, items: list[dict], employee_id: int):
    """
    Simulates a wholesale purchase from HQ (Source) to a Partner (Destination).
    1. Creates a Transaction (Sale) at Source Location (HQ).
       - Uses 'wholesale_price' if available, otherwise 'price'.
    2. Increments Stock at Partner Location.
    
    This is different from a Transfer because it generates Revenue for HQ.
    """
    try:
        # Validate Locations
        source = crud.get_location(db, source_location_id)
        partner = crud.get_location(db, partner_location_id)
        
        if not source or not partner:
            raise ValueError("Invalid locations.")
        if partner.location_type != 'partner':
            raise ValueError("Destination must be a Partner for Wholesale Order.")
            
        # 1. Prepare Items with Wholesale Price
        sale_items = []
        for item in items:
            product = crud.get_product(db, item['product_id'])
            # Priority: item['unit_price'] (manual override) -> product.wholesale_price -> product.price
            unit_price = item.get('unit_price') or product.wholesale_price or product.price
            
            sale_items.append({
                'product_id': item['product_id'],
                'quantity': item['quantity'],
                'unit_price': float(unit_price) 
            })
            
        # 2. Process Sale at Source (Decrement HQ Stock, Record Transaction)
        transaction = process_sale(db, source_location_id, employee_id, sale_items)
        
        # 3. Increment Stock at Partner (The "Deliver" phase)
        # Note: We do this after the sale. If it fails, the sale remains (technically true, Partner paid, 
        # but delivery processing failed - manual intervention needed).
        # For full atomicity, we'd need a bigger distributed transaction or saga logic.
        # Here we just assume success.
        for item in items:
            crud.update_stock(db, partner_location_id, item['product_id'], item['quantity'])
            
        logger.info(f"Wholesale Order completed. Tx: {transaction.id}. Stock moved to Partnmer {partner_location_id}.")
        return transaction
        
    except Exception as e:
        logger.error(f"Wholesale Order failed: {e}")
        raise e

def process_replenishment(db: Session, source_location_id: int, target_location_id: int, items: list[dict], employee_id: int):
    """
    Routes the request based on Target Location Type.
    - Target = Store -> Stock Transfer (Internal movement)
    - Target = Partner -> Wholesale Order (Sale + Delivery)
    """
    target = crud.get_location(db, target_location_id)
    if not target:
        raise ValueError("Target location not found.")
        
    if target.location_type == 'store':
        # Internal Stock Transfer
        transfers = []
        for item in items:
             t = crud.create_stock_transfer(
                db, 
                item['product_id'], 
                source_location_id, 
                target_location_id, 
                item['quantity'], 
                employee_id
            )
             transfers.append(t)
        return {"type": "transfer", "data": transfers}
        
    elif target.location_type == 'partner':
        # Wholesale Order
        tx = create_wholesale_order(db, source_location_id, target_location_id, items, employee_id)
        return {"type": "sale", "data": tx}
        
    else:
        raise ValueError(f"Unknown location type: {target.location_type}")
