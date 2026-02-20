from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# ---- Users ----
class UserCreate(BaseModel):
    name: str
    role: str = "customer"

class UserOut(BaseModel):
    id: int
    name: str
    role: str
    class Config:
        from_attributes = True

# ---- Services ----
class ServiceCreate(BaseModel):
    name: str
    description: str = ""

class ServiceOut(BaseModel):
    id: int
    name: str
    description: str
    class Config:
        from_attributes = True

# ---- Technicians ----
class TechnicianCreate(BaseModel):
    user_id: int
    display_name: str
    bio: str = ""
    service_id: int
    lat: float
    lng: float

class TechnicianUpdate(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    service_id: Optional[int] = None
    lat: Optional[float] = None
    lng: Optional[float] = None

class TechnicianOut(BaseModel):
    id: int
    user_id: int
    display_name: str
    bio: str
    service_id: int
    lat: float
    lng: float
    class Config:
        from_attributes = True

# ---- Certifications ----
class CertificationCreate(BaseModel):
    title: str
    issuer: str
    year: int

class CertificationOut(BaseModel):
    id: int
    technician_id: int
    title: str
    issuer: str
    year: int
    class Config:
        from_attributes = True

# ---- Requests ----
class RequestCreate(BaseModel):
    customer_id: int
    service_id: int
    title: str
    description: str
    lat: float
    lng: float

class RequestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class RequestOut(BaseModel):
    id: int
    customer_id: int
    service_id: int
    title: str
    description: str
    lat: float
    lng: float
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

# ---- Quotations ----
class QuotationCreate(BaseModel):
    technician_id: int
    price: float = Field(gt=0)
    note: str = ""

class QuotationOut(BaseModel):
    id: int
    request_id: int
    technician_id: int
    price: float
    note: str
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

# ---- Jobs ----
class JobOut(BaseModel):
    id: int
    request_id: int
    customer_id: int
    technician_id: int
    quotation_id: int
    status: str
    created_at: datetime
    class Config:
        from_attributes = True

class JobUpdate(BaseModel):
    status: str

# ---- Reviews ----
class ReviewCreate(BaseModel):
    job_id: int
    rating: int = Field(ge=1, le=5)
    comment: str = ""

class ReviewOut(BaseModel):
    id: int
    job_id: int
    customer_id: int
    technician_id: int
    rating: int
    comment: str
    created_at: datetime
    class Config:
        from_attributes = True

# ---- Price Estimate ----
class PriceEstimateOut(BaseModel):
    service_id: int
    average_price: float
    sample_size: int
