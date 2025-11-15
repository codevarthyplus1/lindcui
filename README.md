# KVM/QEMU/OVN Cluster Management System

A comprehensive open-source cluster management system for KVM virtualization with OVN/OVS networking (Layer 2-7).

## Features

### Virtualization
- **KVM/QEMU Host Management**: Manage multiple KVM hosts in a cluster
- **VM Lifecycle Management**: Create, start, stop, pause, resume, and delete VMs
- **Resource Allocation**: CPU, memory, and storage management
- **Live Migration**: Move VMs between hosts (future)

### Networking (L2-L7)
- **OVN Integration**: Software-defined networking using Open Virtual Network
- **OVS Bridges**: Automated Open vSwitch configuration
- **Logical Networks**: Create isolated logical switches and routers
- **Security Groups & ACLs**: Layer 3-4 firewalling
- **Load Balancing**: Layer 4-7 load balancing capabilities
- **Network Topology**: Visual representation of network architecture

### Management Interface
- **Web GUI**: Modern React-based web interface
- **REST API**: Comprehensive API for automation
- **Real-time Monitoring**: Host and VM resource monitoring
- **Dashboard**: Cluster overview and statistics

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Web GUI (React)                   │
└─────────────────────────────────────────────────────┘
                         │
                    REST API
                         │
┌─────────────────────────────────────────────────────┐
│          Backend (FastAPI + Python)                 │
│  ┌──────────────┐  ┌──────────────┐                │
│  │   Cluster    │  │   Network    │                │
│  │  Controller  │  │  Controller  │                │
│  └──────────────┘  └──────────────┘                │
└─────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼──────┐  ┌──────▼─────┐  ┌──────▼─────┐
│  KVM Host 1  │  │ KVM Host 2 │  │ KVM Host N │
│  + libvirt   │  │ + libvirt  │  │ + libvirt  │
│  + OVS/OVN   │  │ + OVS/OVN  │  │ + OVS/OVN  │
└──────────────┘  └────────────┘  └────────────┘
```

## Technology Stack

### Backend
- **Python 3.8+**: Core language
- **FastAPI**: REST API framework
- **libvirt-python**: KVM/QEMU management
- **SQLAlchemy**: Database ORM
- **SQLite/PostgreSQL**: Metadata storage

### Frontend
- **React 18**: UI framework
- **TypeScript**: Type-safe development
- **Material-UI**: Component library
- **D3.js**: Network topology visualization
- **Axios**: HTTP client

### Infrastructure
- **KVM/QEMU**: Virtualization
- **OVS (Open vSwitch)**: Software-defined switching
- **OVN (Open Virtual Network)**: Network virtualization
- **libvirt**: Virtualization API

## Prerequisites

### KVM Hosts
Each host in the cluster needs:
- Linux kernel with KVM support
- QEMU installed
- libvirt daemon running
- Open vSwitch and OVN installed
- SSH access configured

### Management Server
- Python 3.8+
- Node.js 16+ (for frontend)
- Network access to all KVM hosts

## Installation

### 1. Install Dependencies on KVM Hosts

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils \
                    openvswitch-switch ovn-host ovn-central

# Enable and start services
sudo systemctl enable --now libvirtd
sudo systemctl enable --now openvswitch-switch
sudo systemctl enable --now ovn-controller

# RHEL/CentOS/Fedora
sudo dnf install -y qemu-kvm libvirt virt-install openvswitch ovn
sudo systemctl enable --now libvirtd
sudo systemctl enable --now openvswitch
sudo systemctl enable --now ovn-controller
```

### 2. Setup Management Server

```bash
# Clone repository
git clone <repository-url>
cd lindcui

# Install backend dependencies
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure backend
cp config.example.yaml config.yaml
# Edit config.yaml with your cluster details

# Initialize database
python init_db.py

# Start backend API
uvicorn main:app --host 0.0.0.0 --port 8000

# In a new terminal, install and start frontend
cd ../frontend
npm install
npm start
```

### 3. Access Web GUI

Open browser to: `http://localhost:3000`

## Configuration

Edit `backend/config.yaml`:

```yaml
cluster:
  name: "My KVM Cluster"

hosts:
  - name: "kvm-host-1"
    address: "192.168.1.101"
    libvirt_uri: "qemu+ssh://root@192.168.1.101/system"

  - name: "kvm-host-2"
    address: "192.168.1.102"
    libvirt_uri: "qemu+ssh://root@192.168.1.102/system"

ovn:
  nb_db: "tcp:192.168.1.101:6641"  # OVN North database
  sb_db: "tcp:192.168.1.101:6642"  # OVN South database

database:
  url: "sqlite:///./cluster.db"
  # url: "postgresql://user:pass@localhost/cluster_db"

storage:
  default_pool: "default"
  image_path: "/var/lib/libvirt/images"

network:
  default_bridge: "br-int"
  management_network: "192.168.100.0/24"
```

## API Documentation

Once the backend is running, access API docs at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Usage Examples

### Managing Hosts

```python
# Add a new host to the cluster
POST /api/v1/hosts
{
  "name": "kvm-host-3",
  "address": "192.168.1.103",
  "libvirt_uri": "qemu+ssh://root@192.168.1.103/system"
}

# List all hosts
GET /api/v1/hosts

# Get host details
GET /api/v1/hosts/{host_id}
```

### Managing VMs

```python
# Create a new VM
POST /api/v1/vms
{
  "name": "web-server-01",
  "host_id": 1,
  "vcpus": 2,
  "memory": 2048,
  "disk_size": 20,
  "network": "default",
  "os_variant": "ubuntu22.04"
}

# Start VM
POST /api/v1/vms/{vm_id}/start

# Stop VM
POST /api/v1/vms/{vm_id}/stop

# Delete VM
DELETE /api/v1/vms/{vm_id}
```

### Managing Networks

```python
# Create logical switch
POST /api/v1/networks/switches
{
  "name": "web-tier",
  "subnet": "10.0.1.0/24"
}

# Create logical router
POST /api/v1/networks/routers
{
  "name": "main-router"
}

# Create ACL rule
POST /api/v1/networks/acls
{
  "switch": "web-tier",
  "direction": "from-lport",
  "priority": 1000,
  "match": "ip4.src == 10.0.1.0/24 && tcp.dst == 80",
  "action": "allow"
}

# Create load balancer
POST /api/v1/networks/load-balancers
{
  "name": "web-lb",
  "protocol": "tcp",
  "vip": "10.0.1.100:80",
  "backends": ["10.0.1.10:80", "10.0.1.11:80"]
}
```

## Project Structure

```
lindcui/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── requirements.txt        # Python dependencies
│   ├── config.yaml            # Configuration
│   ├── models/                # Database models
│   ├── api/                   # API routes
│   │   ├── hosts.py          # Host management
│   │   ├── vms.py            # VM management
│   │   ├── networks.py       # Network management
│   │   └── cluster.py        # Cluster operations
│   ├── services/             # Business logic
│   │   ├── libvirt_mgr.py   # Libvirt management
│   │   ├── ovn_mgr.py       # OVN management
│   │   ├── ovs_mgr.py       # OVS management
│   │   └── cluster_mgr.py   # Cluster orchestration
│   └── utils/                # Utilities
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/       # React components
│   │   │   ├── Dashboard/   # Dashboard view
│   │   │   ├── Hosts/       # Host management
│   │   │   ├── VMs/         # VM management
│   │   │   ├── Networks/    # Network management
│   │   │   └── Topology/    # Network topology
│   │   ├── services/        # API client
│   │   ├── App.tsx
│   │   └── index.tsx
│   ├── package.json
│   └── tsconfig.json
│
└── README.md
```

## Security Considerations

1. **SSH Key Authentication**: Use SSH keys for libvirt connections
2. **API Authentication**: Implement JWT or OAuth2 for API access
3. **Network Isolation**: Use OVN security groups to isolate VMs
4. **RBAC**: Implement role-based access control
5. **TLS/SSL**: Use HTTPS for web GUI and API

## Roadmap

- [ ] Live VM migration
- [ ] Automated backups and snapshots
- [ ] High availability (HA) support
- [ ] Metrics and monitoring integration (Prometheus/Grafana)
- [ ] Multi-tenant support
- [ ] Kubernetes integration
- [ ] Storage cluster integration (Ceph)
- [ ] Advanced networking (VPNs, VLANs)

## Contributing

Contributions are welcome! Please feel free to submit pull requests.

## License

MIT License

## Support

For issues and questions, please use the GitHub issue tracker.
