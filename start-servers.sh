#!/bin/bash

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Starting Test Environment${NC}"
echo -e "${GREEN}(3 Simulated Servers)${NC}"
echo -e "${GREEN}=========================================${NC}"

# Start backend
echo -e "\n${YELLOW}Starting backend API...${NC}"
cd backend
source venv/bin/activate

# Set test mode to use mock services
export TEST_MODE=1
python main.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo $BACKEND_PID > ../logs/backend.pid

cd ..

echo -e "${GREEN}✓${NC} Backend starting (PID: $BACKEND_PID)"
echo "  Waiting for backend to be ready..."

# Wait for backend
sleep 3
for i in {1..15}; do
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Backend is ready!"
        break
    fi
    if [ $i -eq 15 ]; then
        echo -e "${YELLOW}Backend may still be starting, check logs/backend.log${NC}"
    fi
    sleep 1
done

# Start frontend
echo -e "\n${YELLOW}Starting frontend GUI...${NC}"
cd frontend

npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../logs/frontend.pid

cd ..

echo -e "${GREEN}✓${NC} Frontend starting (PID: $FRONTEND_PID)"
sleep 3

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}Environment Ready!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo -e "\n${YELLOW}Simulated Servers:${NC}"
echo -e "  • server-1.local (test-server-1)"
echo -e "  • server-2.local (test-server-2)"
echo -e "  • server-3.local (test-server-3)"
echo -e "\n${YELLOW}Access Points:${NC}"
echo -e "  Web GUI:    ${GREEN}http://localhost:5173${NC}"
echo -e "  API:        ${GREEN}http://localhost:8000${NC}"
echo -e "  API Docs:   ${GREEN}http://localhost:8000/docs${NC}"
echo -e "\n${YELLOW}Logs:${NC}"
echo -e "  Backend:  tail -f logs/backend.log"
echo -e "  Frontend: tail -f logs/frontend.log"
echo -e "\n${YELLOW}To stop:${NC} ./stop-servers.sh"
echo ""

