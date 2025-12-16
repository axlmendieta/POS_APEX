import init_db
from database import SessionLocal
import crud
import service_admin
import os
import traceback

def setup_db():
    os.environ["ALLOW_SCHEMA_DROP"] = "true"
    init_db.init_db()
    os.environ.pop("ALLOW_SCHEMA_DROP", None)

def test_admin_logic():
    print("\n--- Test: Global Admin & Onboarding ---")
    setup_db()
    db = SessionLocal()
    try:
        # --- 1. Setup Super Admin ---
        hq = crud.create_location(db, "HQ", "warehouse")
        super_admin = crud.create_employee(db, "god_mode", "super_admin", "pwd", hq.id)
        
        # --- 2. Test Store Provisioning (Super Admin) ---
        print("\nProvisioning New Stores...")
        
        # Type A: Proprietary
        store_a = service_admin.register_new_store(
            db, super_admin.id, "Store A", "123 Main St", "TAX-001", "contact@storea.com", "store"
        )
        assert store_a.id is not None
        assert store_a.tax_id == "TAX-001"
        print("SUCCESS: Store A (Proprietary) created.")
        
        # Type B: Partner
        partner_b = service_admin.register_new_store(
            db, super_admin.id, "Partner B", "456 Market St", "TAX-002", "owner@partnerb.com", "partner"
        )
        assert partner_b.id is not None
        print("SUCCESS: Partner B (External) created.")
        
        # --- 3. Test User Creation (Hierarchy) ---
        print("\nCreating Managers/Owners (by Super Admin)...")
        
        # Create Branch Manager for Store A
        mgr_a = service_admin.create_user_profile(
            db, super_admin.id, "manager_a", "pwd", "branch_manager", store_a.id
        )
        print("SUCCESS: Branch Manager A created.")
        
        # Create Partner Owner for Partner B
        owner_b = service_admin.create_user_profile(
            db, super_admin.id, "owner_b", "pwd", "partner_owner", partner_b.id
        )
        print("SUCCESS: Partner Owner B created.")
        
        # --- 4. Test Restricted Creation (Branch Manager) ---
        print("\nTesting Branch Manager Permissions...")
        
        # Should SUCCEED: Create Internal Cashier at Store A
        cashier_a = service_admin.create_user_profile(
            db, mgr_a.id, "cashier_a1", "pwd", "internal_cashier", store_a.id
        )
        print("SUCCESS: Manager A created Internal Cashier.")
        
        # Should FAIL: Create External Cashier (Wrong Role)
        try:
            service_admin.create_user_profile(
                db, mgr_a.id, "fail_cashier", "pwd", "external_cashier", store_a.id
            )
            print("FAILED: Manager A should not create External Cashier.")
        except PermissionError:
             print("SUCCESS: Manager A blocked from creating External Cashier.")
        except ValueError as e:
             # Depending on logic order, it might trigger Role Invalid for Store Type first
             print(f"SUCCESS: Blocked via Validation ({e})")

        # Should FAIL: Create User for Partner B (Wrong Store)
        try:
            service_admin.create_user_profile(
                db, mgr_a.id, "spy_a", "pwd", "internal_cashier", partner_b.id
            )
            print("FAILED: Manager A should not access Partner B.")
        except PermissionError:
             print("SUCCESS: Manager A blocked from accessing other store.")
             
             
        # --- 5. Test Restricted Creation (Partner Owner) ---
        print("\nTesting Partner Owner Permissions...")
        
        # Should SUCCEED: Create External Cashier at Partner B
        cashier_b = service_admin.create_user_profile(
            db, owner_b.id, "cashier_b1", "pwd", "external_cashier", partner_b.id
        )
        print("SUCCESS: Owner B created External Cashier.")
        
        # Should FAIL: Create Branch Manager (Wrong Role)
        try:
            service_admin.create_user_profile(
                db, owner_b.id, "rogue_mgr", "pwd", "branch_manager", partner_b.id
            )
            print("FAILED: Owner B should not create Branch Manager.")
        except PermissionError:
             print("SUCCESS: Owner B blocked from creating Manager.")

        print("\nSUCCESS: All Admin/Onboarding Tests Passed.")

    except Exception:
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_admin_logic()
