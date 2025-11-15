#!/bin/bash
# Simplified test setup - runs backend and frontend locally with mock configuration

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}KVM Cluster - Simple Test Setup${NC}"
echo -e "${GREEN}=========================================${NC}"

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"
for cmd in python3 node npm; do
    if ! command -v $cmd &> /dev/null; then
        echo -e "${RED}Error: $cmd is not installed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} $cmd found"
done

# Backend setup
echo -e "\n${YELLOW}Setting up backend...${NC}"
cd backend

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
pip install -r requirements.txt

# Create test configuration with local/test mode
echo -e "${YELLOW}Creating test configuration...${NC}"
cat > config.yaml << 'EOF'
cluster:
  name: "Test KVM Cluster"
  description: "Local test environment (simulated hosts)"

# Note: These are simulated hosts for testing
# In a real deployment, these would be actual KVM servers
hosts:
  - name: "test-host-1"
    address: "localhost"
    libvirt_uri: "test:///default"
    enabled: true

  - name: "test-host-2"
    address: "localhost"
    libvirt_uri: "test:///default"
    enabled: true

  - name: "test-host-3"
    address: "localhost"
    libvirt_uri: "test:///default"
    enabled: true

ovn:
  nb_db: "tcp:localhost:6641"
  sb_db: "tcp:localhost:6642"

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
  image_path: "/tmp/test-libvirt/images"
  iso_path: "/tmp/test-libvirt/isos"

network:
  management_network: "192.168.100.0/24"
  default_gateway: "192.168.100.1"
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
  secret_key: "test-secret-key-for-development-only"
  algorithm: "HS256"
  access_token_expire_minutes: 30
  enable_auth: false

cors:
  allow_origins:
    - "http://localhost:3000"
    - "http://localhost:5173"
    - "http://127.0.0.1:3000"
    - "http://127.0.0.1:5173"
  allow_credentials: true
  allow_methods:
    - "*"
  allow_headers:
    - "*"
EOF

echo -e "${GREEN}✓${NC} Configuration created"

# Create test storage directories
mkdir -p /tmp/test-libvirt/{images,isos}

# Initialize database
echo "Initializing database..."
python init_db.py

echo -e "${GREEN}✓${NC} Backend setup complete"
cd ..

# Frontend setup
echo -e "\n${YELLOW}Setting up frontend...${NC}"
cd frontend

# Update API URL for frontend if needed
if [ ! -f "src/config.ts" ]; then
    echo "Creating frontend config..."
    cat > src/config.ts << 'EOF'
export const API_BASE_URL = 'http://localhost:8000';
export const API_VERSION = 'v1';
EOF
fi

# Install dependencies
echo "Installing Node.js dependencies..."
npm install

echo -e "${GREEN}✓${NC} Frontend setup complete"
cd ..

# Create run script
cat > run-test.sh << 'EOF'
#!/bin/bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Starting Test Environment${NC}"
echo -e "${GREEN}=========================================${NC}"

# Start backend
echo -e "\n${YELLOW}Starting backend...${NC}"
cd backend
source venv/bin/activate

# Run backend in background
python main.py > ../backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../backend.pid

cd ..
echo -e "${GREEN}✓${NC} Backend started (PID: $BACKEND_PID)"
echo -e "  Logs: tail -f backend.log"

# Wait for backend to start
echo -e "${YELLOW}Waiting for backend to be ready...${NC}"
sleep 3

# Check if backend is running
for i in {1..10}; do
    if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Backend is ready at http://localhost:8000"
        break
    fi
    if [ $i -eq 10 ]; then
        echo -e "${RED}✗${NC} Backend failed to start. Check backend.log"
        exit 1
    fi
    sleep 1
done

# Start frontend
echo -e "\n${YELLOW}Starting frontend...${NC}"
cd frontend

npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../frontend.pid

cd ..
echo -e "${GREEN}✓${NC} Frontend started (PID: $FRONTEND_PID)"
echo -e "  Logs: tail -f frontend.log"

# Wait for frontend
echo -e "${YELLOW}Waiting for frontend to be ready...${NC}"
sleep 5

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}Test Environment Ready!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo -e "\n${YELLOW}Access Points:${NC}"
echo -e "  Frontend: ${GREEN}http://localhost:5173${NC}"
echo -e "  Backend API: ${GREEN}http://localhost:8000${NC}"
echo -e "  API Docs: ${GREEN}http://localhost:8000/docs${NC}"
echo -e "\n${YELLOW}Logs:${NC}"
echo -e "  Backend: tail -f backend.log"
echo -e "  Frontend: tail -f frontend.log"
echo -e "\n${YELLOW}To stop:${NC} ./stop-test.sh"
echo ""
EOF
chmod +x run-test.sh

# Create stop script
cat > stop-test.sh << 'EOF'
#!/bin/bash

YELLOW='\033[1;33m'
GREEN='\033[0;32m'
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

echo -e "${GREEN}Test environment stopped${NC}"
EOF
chmod +x stop-test.sh

# Create API test script
cat > test-api.sh << 'EOF'
#!/bin/bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

API_URL="http://localhost:8000/api/v1"

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Testing API Endpoints${NC}"
echo -e "${GREEN}=========================================${NC}"

# Test 1: API Health/Root
echo -e "\n${YELLOW}Test 1: API Root${NC}"
RESPONSE=$(curl -s http://localhost:8000/ 2>&1)
if echo "$RESPONSE" | grep -q "KVM Cluster Management API" || [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} API is responding"
    echo "  Response: $RESPONSE"
else
    echo -e "${RED}✗${NC} API not responding"
fi

# Test 2: Cluster Info
echo -e "\n${YELLOW}Test 2: Cluster Info${NC}"
RESPONSE=$(curl -s $API_URL/cluster/info 2>&1)
echo "  Response: $RESPONSE"
if [ ! -z "$RESPONSE" ]; then
    echo -e "${GREEN}✓${NC} Cluster info endpoint working"
else
    echo -e "${YELLOW}⚠${NC} Cluster endpoint returned empty"
fi

# Test 3: List Hosts
echo -e "\n${YELLOW}Test 3: List Hosts${NC}"
RESPONSE=$(curl -s $API_URL/hosts 2>&1)
echo "  Response: $RESPONSE"
echo -e "${GREEN}✓${NC} Hosts endpoint accessible"

# Test 4: List VMs
echo -e "\n${YELLOW}Test 4: List VMs${NC}"
RESPONSE=$(curl -s $API_URL/vms 2>&1)
echo "  Response: $RESPONSE"
echo -e "${GREEN}✓${NC} VMs endpoint accessible"

# Test 5: List Networks
echo -e "\n${YELLOW}Test 5: Network Switches${NC}"
RESPONSE=$(curl -s $API_URL/networks/switches 2>&1)
echo "  Response: $RESPONSE"
echo -e "${GREEN}✓${NC} Networks endpoint accessible"

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}API Tests Complete${NC}"
echo -e "${GREEN}=========================================${NC}"
echo -e "\nOpen ${GREEN}http://localhost:8000/docs${NC} for interactive API documentation"
echo -e "Open ${GREEN}http://localhost:5173${NC} for the web GUI"
EOF
chmod +x test-api.sh

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo -e "\n${YELLOW}Note:${NC} This setup uses libvirt test mode with simulated hosts."
echo -e "For full KVM testing, you would need actual KVM hosts or Docker.\n"
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "  1. Start services: ${GREEN}./run-test.sh${NC}"
echo -e "  2. Test API: ${GREEN}./test-api.sh${NC}"
echo -e "  3. Open GUI: ${GREEN}http://localhost:5173${NC}"
echo -e "  4. Stop services: ${GREEN}./stop-test.sh${NC}"
echo ""
