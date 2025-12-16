from database import SessionLocal
import crud
from models import Location

def create_super_admin():
    db = SessionLocal()
    try:
        # 1. Ensure HQ Location exists
        hq = db.query(Location).filter(Location.location_type == 'warehouse').first()
        if not hq:
            print("Creating HQ Location...")
            hq = crud.create_location(db, "Global HQ", "warehouse", "123 Admin St")
        
        # 2. Create Super Admin
        username = "super_admin_user"
        password = "secure_password_123" # In production, hash this!
        
        existing_user = crud.get_employee_by_username(db, username)
        if existing_user:
            print(f"User '{username}' already exists.")
            # Update password for safety/ensuring knowledge
            existing_user.password_hash = password
            db.commit()
            print(f"Password updated for '{username}'.")
        else:
            crud.create_employee(db, username, "super_admin", password, hq.id)
            print(f"User '{username}' created.")

        print("\n--- Credentials ---")
        print(f"Username: {username}")
        print(f"Password: {password}")
        print("-------------------")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_super_admin()
