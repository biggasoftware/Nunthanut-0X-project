from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20), default="customer")  # customer/technician/admin

    technician_profile = relationship("Technician", back_populates="user", uselist=False)

class Service(Base):
    __tablename__ = "services"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    description: Mapped[str] = mapped_column(Text, default="")

class Technician(Base):
    __tablename__ = "technicians"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    display_name: Mapped[str] = mapped_column(String(120))
    bio: Mapped[str] = mapped_column(Text, default="")
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    lat: Mapped[float] = mapped_column(Float, default=0.0)
    lng: Mapped[float] = mapped_column(Float, default=0.0)

    user = relationship("User", back_populates="technician_profile")
    service = relationship("Service")
    certifications = relationship("Certification", back_populates="technician", cascade="all, delete-orphan")

class Certification(Base):
    __tablename__ = "certifications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    technician_id: Mapped[int] = mapped_column(ForeignKey("technicians.id"))
    title: Mapped[str] = mapped_column(String(120))
    issuer: Mapped[str] = mapped_column(String(120))
    year: Mapped[int] = mapped_column(Integer)

    technician = relationship("Technician", back_populates="certifications")

class ServiceRequest(Base):
    __tablename__ = "service_requests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    service_id: Mapped[int] = mapped_column(ForeignKey("services.id"))
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text)
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="OPEN")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Quotation(Base):
    __tablename__ = "quotations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("service_requests.id"))
    technician_id: Mapped[int] = mapped_column(ForeignKey("technicians.id"))
    price: Mapped[float] = mapped_column(Float)
    note: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("service_requests.id"), unique=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    technician_id: Mapped[int] = mapped_column(ForeignKey("technicians.id"))
    quotation_id: Mapped[int] = mapped_column(ForeignKey("quotations.id"))
    status: Mapped[str] = mapped_column(String(20), default="BOOKED")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Review(Base):
    __tablename__ = "reviews"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), unique=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    technician_id: Mapped[int] = mapped_column(ForeignKey("technicians.id"))
    rating: Mapped[int] = mapped_column(Integer)  # 1..5
    comment: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
