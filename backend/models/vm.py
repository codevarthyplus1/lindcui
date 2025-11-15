"""
Virtual Machine database model
"""
from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class VirtualMachine(Base):
    """Virtual Machine model"""
    __tablename__ = "virtual_machines"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Host association
    host_id: Mapped[int] = mapped_column(ForeignKey("hosts.id"))
    host: Mapped["Host"] = relationship(back_populates="virtual_machines")

    # Status
    status: Mapped[str] = mapped_column(String(50), default="stopped")  # running, stopped, paused, error
    autostart: Mapped[bool] = mapped_column(default=False)

    # Resources
    vcpus: Mapped[int] = mapped_column(Integer)
    memory: Mapped[int] = mapped_column(Integer)  # MB
    cpu_usage: Mapped[float] = mapped_column(Float, default=0.0)
    memory_usage: Mapped[float] = mapped_column(Float, default=0.0)

    # Disk
    disk_size: Mapped[int] = mapped_column(Integer)  # GB
    disk_path: Mapped[str] = mapped_column(String(512), nullable=True)
    disk_format: Mapped[str] = mapped_column(String(50), default="qcow2")

    # OS
    os_variant: Mapped[str] = mapped_column(String(100), nullable=True)
    os_type: Mapped[str] = mapped_column(String(50), nullable=True)  # linux, windows, etc

    # Network
    network_interfaces: Mapped[dict] = mapped_column(JSON, default=[])  # List of network interfaces
    ip_addresses: Mapped[dict] = mapped_column(JSON, default=[])

    # VNC/Console
    vnc_port: Mapped[int] = mapped_column(Integer, nullable=True)
    vnc_password: Mapped[str] = mapped_column(String(255), nullable=True)

    # Metadata
    metadata: Mapped[dict] = mapped_column(JSON, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<VirtualMachine {self.name} ({self.uuid})>"
