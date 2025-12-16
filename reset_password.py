from database import SessionLocal
from models import Employee
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def reset_pw():
    db = SessionLocal()
    try:
        # Reset super_admin_user
        u = db.query(Employee).filter(Employee.username == "super_admin_user").first()
        if u:
            # DEMO MODE: api.py compares plain text.
            u.password_hash = "123456" 
            print(f"Reset password for {u.username}")
        
        # Reset api_admin
        u2 = db.query(Employee).filter(Employee.username == "api_admin").first()
        if u2:
            u2.password_hash = "123456"
            print(f"Reset password for {u2.username}")
            
        db.commit()
        
        # Verify
        u_verify = db.query(Employee).filter(Employee.username == "super_admin_user").first()
        print(f"VERIFY: {u_verify.username} pass={u_verify.password_hash}")
    except Exception as e:
        print(e)
    finally:
        db.close()

if __name__ == "__main__":
    reset_pw()
