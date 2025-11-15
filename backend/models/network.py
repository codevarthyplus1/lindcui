"""
Network database models
"""
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, JSON, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class LogicalSwitch(Base):
    """OVN Logical Switch model"""
    __tablename__ = "logical_switches"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Network configuration
    subnet: Mapped[str] = mapped_column(String(50))  # e.g., "10.0.1.0/24"
    gateway: Mapped[str] = mapped_column(String(50), nullable=True)
    dns_servers: Mapped[dict] = mapped_column(JSON, default=[])

    # DHCP
    enable_dhcp: Mapped[bool] = mapped_column(Boolean, default=True)
    dhcp_range_start: Mapped[str] = mapped_column(String(50), nullable=True)
    dhcp_range_end: Mapped[str] = mapped_column(String(50), nullable=True)

    # Metadata
    metadata: Mapped[dict] = mapped_column(JSON, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<LogicalSwitch {self.name} ({self.subnet})>"


class LogicalRouter(Base):
    """OVN Logical Router model"""
    __tablename__ = "logical_routers"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Configuration
    enable_snat: Mapped[bool] = mapped_column(Boolean, default=True)
    external_gateway: Mapped[str] = mapped_column(String(50), nullable=True)

    # Routes
    static_routes: Mapped[dict] = mapped_column(JSON, default=[])

    # Metadata
    metadata: Mapped[dict] = mapped_column(JSON, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<LogicalRouter {self.name}>"


class ACL(Base):
    """OVN ACL (Access Control List) model"""
    __tablename__ = "acls"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Target
    entity_type: Mapped[str] = mapped_column(String(50))  # logical_switch, logical_router, port_group
    entity_name: Mapped[str] = mapped_column(String(255))

    # ACL configuration
    direction: Mapped[str] = mapped_column(String(50))  # from-lport, to-lport
    priority: Mapped[int] = mapped_column(Integer)
    match: Mapped[str] = mapped_column(Text)
    action: Mapped[str] = mapped_column(String(50))  # allow, allow-related, drop, reject

    # Logging
    log: Mapped[bool] = mapped_column(Boolean, default=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=True)

    # Metadata
    metadata: Mapped[dict] = mapped_column(JSON, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ACL {self.name} ({self.action})>"


class LoadBalancer(Base):
    """OVN Load Balancer model (Layer 4-7)"""
    __tablename__ = "load_balancers"

    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Configuration
    protocol: Mapped[str] = mapped_column(String(50))  # tcp, udp, sctp
    vip: Mapped[str] = mapped_column(String(100))  # Virtual IP:port, e.g., "10.0.1.100:80"

    # Backends
    backends: Mapped[dict] = mapped_column(JSON, default=[])  # List of backend IP:port

    # Algorithm
    algorithm: Mapped[str] = mapped_column(String(50), default="round-robin")  # round-robin, least-connections, source-ip

    # Health check
    health_check_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    health_check_interval: Mapped[int] = mapped_column(Integer, nullable=True)
    health_check_timeout: Mapped[int] = mapped_column(Integer, nullable=True)

    # Metadata
    metadata: Mapped[dict] = mapped_column(JSON, default={})
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<LoadBalancer {self.name} ({self.vip})>"
