from sqlalchemy.orm import Session
import crud

from models import Employee, Location
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def register_new_store(db: Session, admin_id: int, name: str, address: str, tax_id: str, contact_info: str, store_type: str):
    """
    Provisions a new store.
    - Validates Supervisor is Super Admin.
    - Creates Location with Type (store/partner).
    """
    try:
        # 1. Auth Check (Super Admin Only)
        admin = crud.get_employee(db, admin_id)
        if not admin or admin.role != 'super_admin':
            raise PermissionError("Only Super Admin can register new stores.")
            
        if store_type not in ['store', 'partner']:
            raise ValueError("Invalid Store Type. Must be 'store' (Proprietary) or 'partner' (External).")

        # 2. Create Location
        location = crud.create_location(
            db, 
            name=name, 
            location_type=store_type, 
            address=address, 
            tax_id=tax_id, 
            contact_info=contact_info
        )
        
        logger.info(f"Store '{name}' ({store_type}) provisioned by Admin {admin_id}. ID: {location.id}")
        return location
        
    except Exception as e:
        logger.error(f"Register Store failed: {e}")
        raise e

def create_user_profile(db: Session, creator_id: int, new_username: str, new_password: str, role: str, target_store_id: int):
    """
    Creates a new user profile with Context-Aware Role Logic.
    
    Hierarchy Rules:
    - Super Admin: Can create ANY role for ANY store.
    - Partner Owner: Can create ONLY 'external_cashier' for THEIR store.
    - Branch Manager: Can create ONLY 'internal_cashier' for THEIR store.
    """
    try:
        creator = crud.get_employee(db, creator_id)
        if not creator:
            raise PermissionError("Creator not found.")
            
        target_store = crud.get_location(db, target_store_id)
        if not target_store:
            raise ValueError("Target Store not found.")
            
        # --- Logic Matrix ---
        
        # 1. Super Admin (God Mode)
        if creator.role == 'super_admin':
            # Basic validation of role vs store type
            if target_store.location_type == 'store' and role not in ['branch_manager', 'internal_cashier']:
                 raise ValueError(f"Role '{role}' invalid for Proprietary Store.")
            if target_store.location_type == 'partner' and role not in ['partner_owner', 'external_cashier']:
                 raise ValueError(f"Role '{role}' invalid for External Partner.")
            if target_store.location_type == 'warehouse' and role not in ['super_admin', 'logistics_manager', 'kam']:
                 raise ValueError(f"Role '{role}' invalid for Warehouse/HQ.")
                 
            # Proceed
            
        # 2. Partner Owner (External)
        elif creator.role == 'partner_owner':
            if creator.assigned_location_id != target_store_id:
                raise PermissionError("Partners can only create users for their own store.")
            
            if role != 'external_cashier':
                raise PermissionError("Partners can only create 'External Cashier' roles.")
                
            if target_store.location_type != 'partner':
                 raise ValueError("Target must be a Partner Location.")

        # 3. Branch Manager (Internal)
        elif creator.role == 'branch_manager':
            if creator.assigned_location_id != target_store_id:
                raise PermissionError("Branch Managers can only create users for their own branch.")
                
            if role != 'internal_cashier':
                raise PermissionError("Branch Managers can only create 'Internal Cashier' roles.")
                
            if target_store.location_type != 'store':
                 raise ValueError("Target must be a Proprietary Store.")
                 
        else:
             raise PermissionError(f"Role '{creator.role}' is not authorized to create users.")

        # --- Execution ---
        new_user = crud.create_employee(
            db, 
            username=new_username, 
            role=role, 
            password_hash=new_password, # Placeholder hashing
            location_id=target_store_id
        )
        
        logger.info(f"User '{new_username}' ({role}) created by {creator.username} for Store {target_store_id}.")
        return new_user

    except Exception as e:
        logger.error(f"Create User Profile failed: {e}")
        raise e
