from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from .database import Base, engine, get_db
from . import models, schemas
from .utils import haversine_km

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Verified Technician REST API")

@app.get("/")
def root():
    return {
        "message": "Verified Technician REST API",
        "docs": "/docs",
        "version": "1.0.0"
    }

# ---------- Users ----------
@app.post("/users", response_model=schemas.UserOut)
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    u = models.User(name=payload.name, role=payload.role)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u

@app.get("/users", response_model=list[schemas.UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(models.User).all()

# ---------- Services CRUD ----------
@app.post("/services", response_model=schemas.ServiceOut)
def create_service(payload: schemas.ServiceCreate, db: Session = Depends(get_db)):
    exists = db.query(models.Service).filter(models.Service.name == payload.name).first()
    if exists:
        raise HTTPException(status_code=409, detail="Service name already exists")
    s = models.Service(name=payload.name, description=payload.description)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s

@app.get("/services", response_model=list[schemas.ServiceOut])
def list_services(db: Session = Depends(get_db)):
    return db.query(models.Service).all()

@app.get("/services/{service_id}", response_model=schemas.ServiceOut)
def get_service(service_id: int, db: Session = Depends(get_db)):
    s = db.get(models.Service, service_id)
    if not s:
        raise HTTPException(404, "Service not found")
    return s

@app.put("/services/{service_id}", response_model=schemas.ServiceOut)
def update_service(service_id: int, payload: schemas.ServiceCreate, db: Session = Depends(get_db)):
    s = db.get(models.Service, service_id)
    if not s:
        raise HTTPException(404, "Service not found")
    s.name = payload.name
    s.description = payload.description
    db.commit()
    db.refresh(s)
    return s

@app.delete("/services/{service_id}")
def delete_service(service_id: int, db: Session = Depends(get_db)):
    s = db.get(models.Service, service_id)
    if not s:
        raise HTTPException(404, "Service not found")
    db.delete(s)
    db.commit()
    return {"deleted": True}

# ---------- Technicians CRUD + Search ----------
@app.post("/technicians", response_model=schemas.TechnicianOut)
def create_technician(payload: schemas.TechnicianCreate, db: Session = Depends(get_db)):
    user = db.get(models.User, payload.user_id)
    if not user:
        raise HTTPException(404, "User not found")
    if user.role not in ("technician", "admin"):
        raise HTTPException(400, "User role must be technician/admin to create technician profile")

    if db.query(models.Technician).filter(models.Technician.user_id == payload.user_id).first():
        raise HTTPException(409, "Technician profile already exists for this user")

    tech = models.Technician(**payload.model_dump())
    db.add(tech)
    db.commit()
    db.refresh(tech)
    return tech

@app.get("/technicians", response_model=list[schemas.TechnicianOut])
def list_technicians(db: Session = Depends(get_db)):
    return db.query(models.Technician).all()

@app.get("/technicians/{tech_id}", response_model=schemas.TechnicianOut)
def get_technician(tech_id: int, db: Session = Depends(get_db)):
    tech = db.get(models.Technician, tech_id)
    if not tech:
        raise HTTPException(404, "Technician not found")
    return tech

@app.put("/technicians/{tech_id}", response_model=schemas.TechnicianOut)
def update_technician(tech_id: int, payload: schemas.TechnicianUpdate, db: Session = Depends(get_db)):
    tech = db.get(models.Technician, tech_id)
    if not tech:
        raise HTTPException(404, "Technician not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(tech, k, v)
    db.commit()
    db.refresh(tech)
    return tech

@app.delete("/technicians/{tech_id}")
def delete_technician(tech_id: int, db: Session = Depends(get_db)):
    tech = db.get(models.Technician, tech_id)
    if not tech:
        raise HTTPException(404, "Technician not found")
    db.delete(tech)
    db.commit()
    return {"deleted": True}

@app.get("/technicians/search", response_model=list[schemas.TechnicianOut])
def search_technicians(
    service_id: int = Query(...),
    lat: float = Query(...),
    lng: float = Query(...),
    radius_km: float = Query(5, gt=0),
    db: Session = Depends(get_db)
):
    techs = db.query(models.Technician).filter(models.Technician.service_id == service_id).all()
    result = []
    for t in techs:
        d = haversine_km(lat, lng, t.lat, t.lng)
        if d <= radius_km:
            result.append(t)
    return result

# ---------- Certifications ----------
@app.post("/technicians/{tech_id}/certifications", response_model=schemas.CertificationOut)
def add_cert(tech_id: int, payload: schemas.CertificationCreate, db: Session = Depends(get_db)):
    tech = db.get(models.Technician, tech_id)
    if not tech:
        raise HTTPException(404, "Technician not found")
    c = models.Certification(technician_id=tech_id, **payload.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return c

@app.get("/technicians/{tech_id}/certifications", response_model=list[schemas.CertificationOut])
def list_certs(tech_id: int, db: Session = Depends(get_db)):
    return db.query(models.Certification).filter(models.Certification.technician_id == tech_id).all()

@app.delete("/certifications/{cert_id}")
def delete_cert(cert_id: int, db: Session = Depends(get_db)):
    c = db.get(models.Certification, cert_id)
    if not c:
        raise HTTPException(404, "Certification not found")
    db.delete(c)
    db.commit()
    return {"deleted": True}

# ---------- Service Requests CRUD ----------
@app.post("/requests", response_model=schemas.RequestOut)
def create_request(payload: schemas.RequestCreate, db: Session = Depends(get_db)):
    customer = db.get(models.User, payload.customer_id)
    if not customer:
        raise HTTPException(404, "Customer not found")
    if customer.role != "customer":
        raise HTTPException(400, "Only customer can create requests")

    req = models.ServiceRequest(**payload.model_dump())
    db.add(req)
    db.commit()
    db.refresh(req)
    return req

@app.get("/requests", response_model=list[schemas.RequestOut])
def list_requests(db: Session = Depends(get_db)):
    return db.query(models.ServiceRequest).all()

@app.get("/requests/{req_id}", response_model=schemas.RequestOut)
def get_request(req_id: int, db: Session = Depends(get_db)):
    req = db.get(models.ServiceRequest, req_id)
    if not req:
        raise HTTPException(404, "Request not found")
    return req

@app.put("/requests/{req_id}", response_model=schemas.RequestOut)
def update_request(req_id: int, payload: schemas.RequestUpdate, db: Session = Depends(get_db)):
    req = db.get(models.ServiceRequest, req_id)
    if not req:
        raise HTTPException(404, "Request not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(req, k, v)
    db.commit()
    db.refresh(req)
    return req

@app.delete("/requests/{req_id}")
def delete_request(req_id: int, db: Session = Depends(get_db)):
    req = db.get(models.ServiceRequest, req_id)
    if not req:
        raise HTTPException(404, "Request not found")
    db.delete(req)
    db.commit()
    return {"deleted": True}

# ---------- Quotations ----------
@app.post("/requests/{req_id}/quotations", response_model=schemas.QuotationOut)
def create_quotation(req_id: int, payload: schemas.QuotationCreate, db: Session = Depends(get_db)):
    req = db.get(models.ServiceRequest, req_id)
    if not req:
        raise HTTPException(404, "Request not found")
    if req.status in ("COMPLETED", "CANCELED"):
        raise HTTPException(400, "Cannot quote closed request")

    tech = db.get(models.Technician, payload.technician_id)
    if not tech:
        raise HTTPException(404, "Technician not found")
    if tech.service_id != req.service_id:
        raise HTTPException(400, "Technician service does not match request service")

    q = models.Quotation(request_id=req_id, **payload.model_dump())
    db.add(q)
    # optional: set request status
    req.status = "QUOTED"
    db.commit()
    db.refresh(q)
    return q

@app.get("/requests/{req_id}/quotations", response_model=list[schemas.QuotationOut])
def list_quotations(req_id: int, db: Session = Depends(get_db)):
    return db.query(models.Quotation).filter(models.Quotation.request_id == req_id).all()

@app.post("/quotations/{quote_id}/accept", response_model=schemas.JobOut)
def accept_quotation(quote_id: int, db: Session = Depends(get_db)):
    q = db.get(models.Quotation, quote_id)
    if not q:
        raise HTTPException(404, "Quotation not found")
    if q.status != "PENDING":
        raise HTTPException(400, "Quotation is not pending")

    req = db.get(models.ServiceRequest, q.request_id)
    if not req:
        raise HTTPException(404, "Request not found")

    # reject other quotations for same request
    db.query(models.Quotation).filter(
        models.Quotation.request_id == req.id,
        models.Quotation.id != q.id
    ).update({"status": "REJECTED"})

    q.status = "ACCEPTED"
    req.status = "BOOKED"

    # create job (1 request -> 1 job)
    if db.query(models.Job).filter(models.Job.request_id == req.id).first():
        raise HTTPException(409, "Job already exists for this request")

    job = models.Job(
        request_id=req.id,
        customer_id=req.customer_id,
        technician_id=q.technician_id,
        quotation_id=q.id,
        status="BOOKED",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

# ---------- Jobs ----------
@app.get("/jobs", response_model=list[schemas.JobOut])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(models.Job).all()

@app.get("/jobs/{job_id}", response_model=schemas.JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(models.Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job

@app.put("/jobs/{job_id}", response_model=schemas.JobOut)
def update_job(job_id: int, payload: schemas.JobUpdate, db: Session = Depends(get_db)):
    job = db.get(models.Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    job.status = payload.status
    # keep request status in sync if completed
    if payload.status == "COMPLETED":
        req = db.get(models.ServiceRequest, job.request_id)
        if req:
            req.status = "COMPLETED"
    db.commit()
    db.refresh(job)
    return job

@app.post("/jobs/{job_id}/complete", response_model=schemas.JobOut)
def complete_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(models.Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    job.status = "COMPLETED"
    req = db.get(models.ServiceRequest, job.request_id)
    if req:
        req.status = "COMPLETED"
    db.commit()
    db.refresh(job)
    return job

# ---------- Reviews (Verified) ----------
@app.post("/reviews", response_model=schemas.ReviewOut)
def create_review(payload: schemas.ReviewCreate, db: Session = Depends(get_db)):
    job = db.get(models.Job, payload.job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job.status != "COMPLETED":
        raise HTTPException(400, "Review allowed only when job is COMPLETED")

    if db.query(models.Review).filter(models.Review.job_id == job.id).first():
        raise HTTPException(409, "Review already exists for this job")

    review = models.Review(
        job_id=job.id,
        customer_id=job.customer_id,
        technician_id=job.technician_id,
        rating=payload.rating,
        comment=payload.comment
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review

@app.get("/technicians/{tech_id}/reviews", response_model=list[schemas.ReviewOut])
def list_reviews(tech_id: int, db: Session = Depends(get_db)):
    return db.query(models.Review).filter(models.Review.technician_id == tech_id).all()

@app.delete("/reviews/{review_id}")
def delete_review(review_id: int, db: Session = Depends(get_db)):
    r = db.get(models.Review, review_id)
    if not r:
        raise HTTPException(404, "Review not found")
    db.delete(r)
    db.commit()
    return {"deleted": True}

# ---------- Price Estimation ----------
@app.get("/price-estimate", response_model=schemas.PriceEstimateOut)
def price_estimate(service_id: int, db: Session = Depends(get_db)):
    # avg from quotations where request.service_id matches
    avg_price, count = db.query(
        func.avg(models.Quotation.price),
        func.count(models.Quotation.id)
    ).join(models.ServiceRequest, models.ServiceRequest.id == models.Quotation.request_id
    ).filter(models.ServiceRequest.service_id == service_id).first()

    if not count or count == 0:
        return {"service_id": service_id, "average_price": 0.0, "sample_size": 0}

    return {"service_id": service_id, "average_price": float(avg_price), "sample_size": int(count)}
