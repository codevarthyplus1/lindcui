"""
Configuration management using Pydantic Settings
"""
from typing import List, Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import yaml
from pathlib import Path


class HostConfig(BaseModel):
    """Host configuration"""
    name: str
    address: str
    libvirt_uri: str
    enabled: bool = True


class ClusterConfig(BaseModel):
    """Cluster configuration"""
    name: str
    description: str = ""


class OVNConfig(BaseModel):
    """OVN configuration"""
    nb_db: str
    sb_db: str
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    ssl_ca: Optional[str] = None


class OVSConfig(BaseModel):
    """OVS configuration"""
    integration_bridge: str = "br-int"
    external_bridge: str = "br-ex"


class DatabaseConfig(BaseModel):
    """Database configuration"""
    url: str
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10


class StorageConfig(BaseModel):
    """Storage configuration"""
    default_pool: str = "default"
    image_path: str = "/var/lib/libvirt/images"
    iso_path: str = "/var/lib/libvirt/isos"


class NetworkConfig(BaseModel):
    """Network configuration"""
    management_network: str
    default_gateway: str
    dns_servers: List[str] = ["8.8.8.8", "8.8.4.4"]


class APIConfig(BaseModel):
    """API configuration"""
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    workers: int = 4
    log_level: str = "info"


class SecurityConfig(BaseModel):
    """Security configuration"""
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    enable_auth: bool = False


class CORSConfig(BaseModel):
    """CORS configuration"""
    allow_origins: List[str] = ["*"]
    allow_credentials: bool = True
    allow_methods: List[str] = ["*"]
    allow_headers: List[str] = ["*"]


class Settings(BaseSettings):
    """Application settings"""
    cluster: ClusterConfig
    hosts: List[HostConfig] = []
    ovn: OVNConfig
    ovs: OVSConfig
    database: DatabaseConfig
    storage: StorageConfig
    network: NetworkConfig
    api: APIConfig
    security: SecurityConfig
    cors: CORSConfig

    @classmethod
    def from_yaml(cls, config_path: str = "config.yaml"):
        """Load settings from YAML file"""
        path = Path(config_path)

        if not path.exists():
            # Try example config
            path = Path("config.example.yaml")
            if not path.exists():
                raise FileNotFoundError(
                    "Configuration file not found. Please create config.yaml from config.example.yaml"
                )

        with open(path, 'r') as f:
            config_data = yaml.safe_load(f)

        return cls(**config_data)


# Load settings from YAML
try:
    settings = Settings.from_yaml()
except FileNotFoundError as e:
    # Provide default settings for development
    print(f"Warning: {e}")
    print("Using default development settings")

    settings = Settings(
        cluster=ClusterConfig(name="Development Cluster", description="Dev cluster"),
        ovn=OVNConfig(nb_db="tcp:127.0.0.1:6641", sb_db="tcp:127.0.0.1:6642"),
        ovs=OVSConfig(),
        database=DatabaseConfig(url="sqlite+aiosqlite:///./cluster.db"),
        storage=StorageConfig(),
        network=NetworkConfig(
            management_network="192.168.100.0/24",
            default_gateway="192.168.100.1"
        ),
        api=APIConfig(),
        security=SecurityConfig(secret_key="dev-secret-key-change-in-production"),
        cors=CORSConfig()
    )
