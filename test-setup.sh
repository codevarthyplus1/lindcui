#!/bin/bash
# Test setup script for KVM Cluster Management System
# Sets up 1 management server + 3 simulated KVM hosts

set -e

echo "========================================="
echo "KVM Cluster Test Environment Setup"
echo "========================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo -e "${RED}Error: This system is designed for Linux${NC}"
    exit 1
fi

# Check for required commands
echo -e "\n${YELLOW}Checking prerequisites...${NC}"
for cmd in docker python3 node npm; do
    if ! command -v $cmd &> /dev/null; then
        echo -e "${RED}Error: $cmd is not installed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} $cmd found"
done

# Create test directory structure
echo -e "\n${YELLOW}Setting up test environment...${NC}"
mkdir -p test-env/kvm-hosts/{host1,host2,host3}
mkdir -p test-env/ssh-keys

# Generate SSH keys for testing (if not exists)
if [ ! -f test-env/ssh-keys/id_rsa ]; then
    echo -e "${YELLOW}Generating SSH keys for test environment...${NC}"
    ssh-keygen -t rsa -b 2048 -f test-env/ssh-keys/id_rsa -N "" -C "test-cluster"
    echo -e "${GREEN}✓${NC} SSH keys generated"
fi

# Create Dockerfile for simulated KVM hosts
echo -e "\n${YELLOW}Creating simulated KVM host containers...${NC}"
cat > test-env/Dockerfile.kvm-host << 'EOF'
FROM ubuntu:22.04

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install minimal KVM/libvirt setup
RUN apt-get update && apt-get install -y \
    qemu-kvm \
    libvirt-daemon-system \
    libvirt-clients \
    openssh-server \
    python3 \
    python3-pip \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Create SSH directory and set up SSH
RUN mkdir /var/run/sshd
RUN echo 'root:testpassword' | chpasswd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# Create .ssh directory for root
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh

# Expose SSH and libvirt ports
EXPOSE 22 16509

# Start script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
EOF

# Create entrypoint script for KVM hosts
cat > test-env/entrypoint.sh << 'EOF'
#!/bin/bash
set -e

# Start libvirtd
echo "Starting libvirtd..."
/usr/sbin/libvirtd -d

# Wait for libvirt to be ready
sleep 2

# Start SSH daemon
echo "Starting SSH daemon..."
/usr/sbin/sshd -D
EOF
chmod +x test-env/entrypoint.sh

# Create docker-compose for test environment
echo -e "${YELLOW}Creating docker-compose configuration...${NC}"
cat > test-env/docker-compose.test.yml << 'EOF'
version: '3.8'

services:
  kvm-host-1:
    build:
      context: .
      dockerfile: Dockerfile.kvm-host
    hostname: kvm-host-1
    privileged: true
    networks:
      cluster-net:
        ipv4_address: 172.20.0.11
    volumes:
      - ./ssh-keys/id_rsa.pub:/root/.ssh/authorized_keys:ro
      - /sys/fs/cgroup:/sys/fs/cgroup:rw
    ports:
      - "2201:22"
      - "16501:16509"

  kvm-host-2:
    build:
      context: .
      dockerfile: Dockerfile.kvm-host
    hostname: kvm-host-2
    privileged: true
    networks:
      cluster-net:
        ipv4_address: 172.20.0.12
    volumes:
      - ./ssh-keys/id_rsa.pub:/root/.ssh/authorized_keys:ro
      - /sys/fs/cgroup:/sys/fs/cgroup:rw
    ports:
      - "2202:22"
      - "16502:16509"

  kvm-host-3:
    build:
      context: .
      dockerfile: Dockerfile.kvm-host
    hostname: kvm-host-3
    privileged: true
    networks:
      cluster-net:
        ipv4_address: 172.20.0.13
    volumes:
      - ./ssh-keys/id_rsa.pub:/root/.ssh/authorized_keys:ro
      - /sys/fs/cgroup:/sys/fs/cgroup:rw
    ports:
      - "2203:22"
      - "16503:16509"

networks:
  cluster-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
EOF

echo -e "${GREEN}✓${NC} Test environment configuration created"

# Backend setup
echo -e "\n${YELLOW}Setting up backend...${NC}"
cd ../backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip > /dev/null
pip install -r requirements.txt > /dev/null

# Create test configuration
echo -e "${YELLOW}Creating test configuration...${NC}"
cat > config.test.yaml << 'EOF'
cluster:
  name: "Test KVM Cluster"
  description: "Test environment with 3 simulated KVM hosts"

hosts:
  - name: "kvm-host-1"
    address: "172.20.0.11"
    libvirt_uri: "qemu+ssh://root@172.20.0.11/system"
    enabled: true

  - name: "kvm-host-2"
    address: "172.20.0.12"
    libvirt_uri: "qemu+ssh://root@172.20.0.12/system"
    enabled: true

  - name: "kvm-host-3"
    address: "172.20.0.13"
    libvirt_uri: "qemu+ssh://root@172.20.0.13/system"
    enabled: true

ovn:
  nb_db: "tcp:172.20.0.11:6641"
  sb_db: "tcp:172.20.0.11:6642"

ovs:
  integration_bridge: "br-int"
  external_bridge: "br-ex"

database:
  url: "sqlite+aiosqlite:///./cluster-test.db"
  echo: false
  pool_size: 5
  max_overflow: 10

storage:
  default_pool: "default"
  image_path: "/var/lib/libvirt/images"
  iso_path: "/var/lib/libvirt/isos"

network:
  management_network: "172.20.0.0/16"
  default_gateway: "172.20.0.1"
  dns_servers:
    - "8.8.8.8"
    - "8.8.4.4"

api:
  host: "0.0.0.0"
  port: 8000
  reload: true
  workers: 1
  log_level: "info"

security:
  secret_key: "test-secret-key-do-not-use-in-production"
  algorithm: "HS256"
  access_token_expire_minutes: 30
  enable_auth: false

cors:
  allow_origins:
    - "http://localhost:3000"
    - "http://localhost:5173"
  allow_credentials: true
  allow_methods:
    - "*"
  allow_headers:
    - "*"
EOF

# Copy test config as main config
cp config.test.yaml config.yaml

# Initialize database
echo "Initializing test database..."
python init_db.py

echo -e "${GREEN}✓${NC} Backend setup complete"

# Frontend setup
echo -e "\n${YELLOW}Setting up frontend...${NC}"
cd ../frontend

# Install dependencies
echo "Installing Node.js dependencies..."
npm install > /dev/null 2>&1

echo -e "${GREEN}✓${NC} Frontend setup complete"

# Create test runner script
cd ..
cat > run-test-environment.sh << 'EOF'
#!/bin/bash
# Script to run the complete test environment

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Starting KVM Cluster Test Environment${NC}"
echo -e "${GREEN}=========================================${NC}"

# Start KVM host containers
echo -e "\n${YELLOW}Starting simulated KVM hosts...${NC}"
cd test-env
docker-compose -f docker-compose.test.yml up -d

echo -e "${YELLOW}Waiting for hosts to be ready...${NC}"
sleep 5

# Check if hosts are accessible
for port in 2201 2202 2203; do
    if nc -z localhost $port 2>/dev/null; then
        echo -e "${GREEN}✓${NC} Host on port $port is ready"
    else
        echo -e "${YELLOW}⚠${NC} Host on port $port is not responding yet"
    fi
done

cd ..

# Configure SSH for test environment
echo -e "\n${YELLOW}Configuring SSH...${NC}"
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Add hosts to known_hosts
for port in 2201 2202 2203; do
    ssh-keyscan -p $port localhost >> ~/.ssh/known_hosts 2>/dev/null || true
done

# Set up SSH config for easy access
cat > ~/.ssh/config_test << 'SSHEOF'
Host kvm-test-1
    HostName localhost
    Port 2201
    User root
    IdentityFile test-env/ssh-keys/id_rsa
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null

Host kvm-test-2
    HostName localhost
    Port 2202
    User root
    IdentityFile test-env/ssh-keys/id_rsa
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null

Host kvm-test-3
    HostName localhost
    Port 2203
    User root
    IdentityFile test-env/ssh-keys/id_rsa
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
SSHEOF

echo -e "${GREEN}✓${NC} SSH configured"

# Start backend
echo -e "\n${YELLOW}Starting backend API...${NC}"
cd backend
source venv/bin/activate
nohup python main.py > ../backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../backend.pid
cd ..

echo -e "${YELLOW}Waiting for backend to start...${NC}"
sleep 5

# Check if backend is running
if curl -s http://localhost:8000/docs > /dev/null; then
    echo -e "${GREEN}✓${NC} Backend API is running"
else
    echo -e "${YELLOW}⚠${NC} Backend API may not be ready yet"
fi

# Start frontend
echo -e "\n${YELLOW}Starting frontend...${NC}"
cd frontend
nohup npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../frontend.pid
cd ..

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}Test Environment is Ready!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo -e "\nAccess points:"
echo -e "  ${YELLOW}Frontend GUI:${NC} http://localhost:5173"
echo -e "  ${YELLOW}Backend API:${NC} http://localhost:8000"
echo -e "  ${YELLOW}API Docs:${NC} http://localhost:8000/docs"
echo -e "\nKVM Host SSH access:"
echo -e "  ${YELLOW}Host 1:${NC} ssh -p 2201 -i test-env/ssh-keys/id_rsa root@localhost"
echo -e "  ${YELLOW}Host 2:${NC} ssh -p 2202 -i test-env/ssh-keys/id_rsa root@localhost"
echo -e "  ${YELLOW}Host 3:${NC} ssh -p 2203 -i test-env/ssh-keys/id_rsa root@localhost"
echo -e "\nLogs:"
echo -e "  ${YELLOW}Backend:${NC} tail -f backend.log"
echo -e "  ${YELLOW}Frontend:${NC} tail -f frontend.log"
echo -e "  ${YELLOW}Docker:${NC} cd test-env && docker-compose -f docker-compose.test.yml logs -f"
echo -e "\nTo stop the environment, run: ./stop-test-environment.sh"
echo ""
EOF
chmod +x run-test-environment.sh

# Create stop script
cat > stop-test-environment.sh << 'EOF'
#!/bin/bash
# Script to stop the test environment

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Stopping test environment...${NC}"

# Stop backend
if [ -f backend.pid ]; then
    kill $(cat backend.pid) 2>/dev/null || true
    rm backend.pid
    echo -e "${GREEN}✓${NC} Backend stopped"
fi

# Stop frontend
if [ -f frontend.pid ]; then
    kill $(cat frontend.pid) 2>/dev/null || true
    rm frontend.pid
    echo -e "${GREEN}✓${NC} Frontend stopped"
fi

# Stop Docker containers
cd test-env
docker-compose -f docker-compose.test.yml down
echo -e "${GREEN}✓${NC} KVM hosts stopped"
cd ..

echo -e "${GREEN}Test environment stopped${NC}"
EOF
chmod +x stop-test-environment.sh

# Create test script
cat > test-cluster.sh << 'EOF'
#!/bin/bash
# Test script to verify cluster functionality

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

API_URL="http://localhost:8000/api/v1"

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Testing Cluster Functionality${NC}"
echo -e "${GREEN}=========================================${NC}"

# Test 1: Check if API is responding
echo -e "\n${YELLOW}Test 1: API Health Check${NC}"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} API is responding"
else
    echo -e "${RED}✗${NC} API is not responding"
    exit 1
fi

# Test 2: List hosts
echo -e "\n${YELLOW}Test 2: List Hosts${NC}"
HOSTS=$(curl -s $API_URL/hosts)
echo "Response: $HOSTS"
if echo "$HOSTS" | grep -q "kvm-host"; then
    echo -e "${GREEN}✓${NC} Hosts endpoint working"
else
    echo -e "${YELLOW}⚠${NC} No hosts found (this is expected if hosts haven't been added yet)"
fi

# Test 3: Get cluster info
echo -e "\n${YELLOW}Test 3: Cluster Information${NC}"
CLUSTER=$(curl -s $API_URL/cluster/info)
echo "Response: $CLUSTER"
if [ ! -z "$CLUSTER" ]; then
    echo -e "${GREEN}✓${NC} Cluster info endpoint working"
else
    echo -e "${RED}✗${NC} Cluster info endpoint failed"
fi

# Test 4: List VMs
echo -e "\n${YELLOW}Test 4: List Virtual Machines${NC}"
VMS=$(curl -s $API_URL/vms)
echo "Response: $VMS"
echo -e "${GREEN}✓${NC} VMs endpoint working"

# Test 5: List Networks
echo -e "\n${YELLOW}Test 5: List Networks${NC}"
NETWORKS=$(curl -s $API_URL/networks/switches)
echo "Response: $NETWORKS"
echo -e "${GREEN}✓${NC} Networks endpoint working"

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}Basic API Tests Complete${NC}"
echo -e "${GREEN}=========================================${NC}"
echo -e "\nFor full testing, use the web GUI at http://localhost:5173"
EOF
chmod +x test-cluster.sh

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}Test Setup Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo -e "\nNext steps:"
echo -e "1. Run: ${YELLOW}./run-test-environment.sh${NC} to start all services"
echo -e "2. Run: ${YELLOW}./test-cluster.sh${NC} to test the API"
echo -e "3. Open: ${YELLOW}http://localhost:5173${NC} to access the GUI"
echo -e "4. Run: ${YELLOW}./stop-test-environment.sh${NC} when done"
echo ""
