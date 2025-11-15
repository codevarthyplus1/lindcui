"""
Host database model
"""
from datetime import datetime
from typing import List
from sqlalchemy import String, Boolean, Integer, Float, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Host(Base):
    """KVM host model"""
    __tablename__ = "hosts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    address: Mapped[str] = mapped_column(String(255))
    libvirt_uri: Mapped[str] = mapped_column(String(512))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)

    # Status
    status: Mapped[str] = mapped_column(String(50), default="unknown")  # online, offline, error
    last_seen: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Resources
    cpu_cores: Mapped[int] = mapped_column(Integer, default=0)
    cpu_threads: Mapped[int] = mapped_column(Integer, default=0)
    cpu_usage: Mapped[float] = mapped_column(Float, default=0.0)

    memory_total: Mapped[int] = mapped_column(Integer, default=0)  # MB
    memory_used: Mapped[int] = mapped_column(Integer, default=0)   # MB
    memory_free: Mapped[int] = mapped_column(Integer, default=0)   # MB

    # Metadata
    metadata: Mapped[dict] = mapped_column(JSON, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    virtual_machines: Mapped[List["VirtualMachine"]] = relationship(back_populates="host", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Host {self.name} ({self.address})>"
