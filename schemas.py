from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- Auth ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str
    role: str
    target_store_id: int

# --- Store Provisioning ---
class StoreCreate(BaseModel):
    name: str
    store_type: str # 'store' or 'partner'
    address: str
    tax_id: str
    contact_info: str

class StoreResponse(BaseModel):
    id: int
    name: str
    location_type: str
    tax_id: Optional[str] = None
    
    class Config:
        from_attributes = True

# --- Sales ---
class SaleItem(BaseModel):
    product_id: int
    quantity: int
    unit_price: Optional[float] = None

class SaleRequest(BaseModel):
    selling_location_id: int
    items: List[SaleItem]
    customer_id: Optional[int] = None

class TransactionResponse(BaseModel):
    id: int
    total_amount: float
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# --- Inventory ---
class ReplenishmentRequest(BaseModel):
    source_location_id: int
    target_location_id: int
    items: List[SaleItem]

# --- Recommendation ---
class RecommendationRequest(BaseModel):
    location_id: int
    customer_id: Optional[int] = None
    cart_items: List[SaleItem]

class UpsellOffer(BaseModel):
    recommendation_active: bool
    suggested_product_id: int
    suggested_product_name: str
    reason: str
    reason_code: str
    original_price: float
    special_offer_price: float
    promo_tag: str
