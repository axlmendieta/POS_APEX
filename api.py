from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Annotated

import crud
import schemas
import service_logic
import service_admin
import recommendation_engine
from database import SessionLocal
import init_db
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="POS System API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve Static Files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
async def read_index():
    return FileResponse('frontend/pos.html')

@app.get("/app")
async def read_client_app():
    return FileResponse('frontend/client_app.html')

@app.get("/styles.css")
async def read_css():
    return FileResponse('frontend/styles.css')

@app.get("/app.js")
async def read_js():
    return FileResponse('frontend/app.js')

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Auth config (Simplified for Demo)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    # In production, verify JWT signature here
    # For this demo, token IS the username (Very insecure, but proof of concept)
    user = db.query(crud.Employee).filter(crud.Employee.username == token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

# --- Routes ---

@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)):
    user = crud.get_employee_by_username(db, form_data.username)
        
    if not user or user.password_hash != form_data.password: # Hashing skipped for demo
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Return username as token for simplicity in this non-JWT demo
    return {"access_token": user.username, "token_type": "bearer"}

@app.post("/sales", response_model=schemas.TransactionResponse, status_code=status.HTTP_201_CREATED)
def process_sale_endpoint(sale_req: schemas.SaleRequest, current_user: Annotated[crud.Employee, Depends(get_current_user)], db: Session = Depends(get_db)):
    try:
        # Convert Pydantic items to list of dicts, populating unit_price if missing
        items_dict = []
        for item in sale_req.items:
            data = item.model_dump()
            if data['unit_price'] is None:
                prod = crud.get_product(db, item.product_id)
                if not prod:
                    raise ValueError(f"Product {item.product_id} not found")
                data['unit_price'] = float(prod.price)
            items_dict.append(data)
        
        tx = service_logic.process_sale(
            db, 
            sale_req.selling_location_id, 
            current_user.id, 
            items_dict, 
            sale_req.customer_id
        )
        # Re-fetch to guarantee attachment after commit
        db.refresh(tx)
        
        return schemas.TransactionResponse(
            id=tx.id,
            total_amount=tx.total_amount,
            status=tx.status,
            created_at=tx.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/admin/stores", response_model=schemas.StoreResponse)
def create_store(store: schemas.StoreCreate, current_user: Annotated[crud.Employee, Depends(get_current_user)], db: Session = Depends(get_db)):
    try:
        new_loc = service_admin.register_new_store(
            db, 
            current_user.id, 
            store.name, 
            store.address, 
            store.tax_id, 
            store.contact_info, 
            store.store_type
        )
        return new_loc
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not Authorized")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/admin/users")
def create_user(user: schemas.UserCreate, current_user: Annotated[crud.Employee, Depends(get_current_user)], db: Session = Depends(get_db)):
    try:
        new_user = service_admin.create_user_profile(
            db, 
            current_user.id, 
            user.username, 
            user.password, 
            user.role, 
            user.target_store_id
        )
        return {"username": new_user.username, "id": new_user.id}
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not Authorized")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/loyalty/upsell", response_model=schemas.UpsellOffer)
def get_upsell(req: schemas.RecommendationRequest, db: Session = Depends(get_db)):
    # No auth required for upsell check? Or maybe yes. usually POS machine is authenticated.
    # We'll skip auth for this endpoint to simulate "Kiosk Mode" or just passing through.
    
    items_dict = [item.model_dump() for item in req.cart_items]
    offer = recommendation_engine.generate_upsell_offer(
        db, 
        req.location_id, 
        req.customer_id, 
        items_dict
    )
    
    if not offer:
        # Return HTTP 204 or just a "No Offer" structure? 
        # Pydantic expects model. Let's return empty/false.
        # But schemas.UpsellOffer requires fields.
        # Better to return 204 No Content if no offer.
        raise HTTPException(status_code=204, detail="No recommendation")
        
    return offer

@app.get("/reports/daily")
def get_daily_reports(current_user: Annotated[crud.Employee, Depends(get_current_user)], db: Session = Depends(get_db)):
    # Simple check: Only Managers/Admins/Owners can see reports
    if current_user.role not in ['branch_manager', 'super_admin', 'partner_owner']:
        raise HTTPException(status_code=403, detail="Not authorized to view reports")
        
    stats = crud.get_daily_sales_stats(db, current_user.assigned_location_id or 1) # Default to 1 for super_admin if None
    recent = crud.get_recent_transactions(db, current_user.assigned_location_id or 1)
    
    return {
        "stats": stats,
        "recent_transactions": [
            {
                "id": t.id,
                "total_amount": t.total_amount,
                "created_at": t.created_at,
                "item_count": len(t.details)
            } for t in recent
        ]
    }

# --- Analytics Endpoints ---
@app.get("/analytics/sales-over-time")
def analytics_sales_over_time(days: int = 7, current_user: Annotated[crud.Employee, Depends(get_current_user)] = None, db: Session = Depends(get_db)):
    if current_user.role not in ['branch_manager', 'super_admin', 'partner_owner']:
        raise HTTPException(status_code=403, detail="Not authorized")
    # Hardcoded Loc 1 for demo
    return crud.get_sales_over_time(db, location_id=1, days=days)

@app.get("/analytics/top-products")
def analytics_top_products(limit: int = 10, current_user: Annotated[crud.Employee, Depends(get_current_user)] = None, db: Session = Depends(get_db)):
    if current_user.role not in ['branch_manager', 'super_admin', 'partner_owner']:
        raise HTTPException(status_code=403, detail="Not authorized")
    return crud.get_top_products(db, location_id=1, limit=limit)

@app.get("/analytics/kpis")
def analytics_kpis(current_user: Annotated[crud.Employee, Depends(get_current_user)] = None, db: Session = Depends(get_db)):
    if current_user.role not in ['branch_manager', 'super_admin', 'partner_owner']:
        raise HTTPException(status_code=403, detail="Not authorized")
    return crud.get_dashboard_kpis(db, location_id=1)

@app.get("/analytics/categories")
def analytics_categories(current_user: Annotated[crud.Employee, Depends(get_current_user)] = None, db: Session = Depends(get_db)):
    if current_user.role not in ['branch_manager', 'super_admin', 'partner_owner']:
        raise HTTPException(status_code=403, detail="Not authorized")
    return crud.get_sales_by_category(db, location_id=1)

@app.get("/inventory")
def get_inventory(current_user: Annotated[crud.Employee, Depends(get_current_user)] = None, db: Session = Depends(get_db)):
    # Inventory is visible to all authenticated employees
    return crud.get_inventory_levels(db, location_id=1)

@app.get("/analytics/locations")
def analytics_locations(current_user: Annotated[crud.Employee, Depends(get_current_user)] = None, db: Session = Depends(get_db)):
    if current_user.role not in ['branch_manager', 'super_admin', 'partner_owner']:
        raise HTTPException(status_code=403, detail="Not authorized")
    return crud.get_revenue_by_location(db)

@app.get("/health")
def health_check():
    return {"status": "ok"}
