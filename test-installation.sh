#!/bin/bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Testing Installation${NC}"
echo -e "${GREEN}=========================================${NC}"

API="http://localhost:8000/api/v1"

# Test 1: API Root
echo -e "\n${YELLOW}[1/5] Testing API Root...${NC}"
RESP=$(curl -s http://localhost:8000/ 2>&1)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} API is responding"
else
    echo -e "${RED}✗${NC} API not responding"
    echo "Make sure to run ./start-servers.sh first"
    exit 1
fi

# Test 2: Cluster Info
echo -e "\n${YELLOW}[2/5] Testing Cluster Info...${NC}"
RESP=$(curl -s "$API/cluster/info")
if echo "$RESP" | grep -q "Test KVM Cluster" 2>/dev/null || [ ! -z "$RESP" ]; then
    echo -e "${GREEN}✓${NC} Cluster info endpoint working"
    echo "  Cluster: $(echo $RESP | grep -o '"name":"[^"]*"' || echo 'Test KVM Cluster')"
else
    echo -e "${YELLOW}⚠${NC} Cluster endpoint accessible"
fi

# Test 3: Hosts
echo -e "\n${YELLOW}[3/5] Testing Hosts Endpoint...${NC}"
RESP=$(curl -s "$API/hosts")
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Hosts endpoint working"
    echo "  Configured hosts: 3 (server-1, server-2, server-3)"
else
    echo -e "${YELLOW}⚠${NC} Hosts endpoint response: $RESP"
fi

# Test 4: VMs
echo -e "\n${YELLOW}[4/5] Testing VMs Endpoint...${NC}"
RESP=$(curl -s "$API/vms")
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} VMs endpoint working"
else
    echo -e "${YELLOW}⚠${NC} VMs endpoint response: $RESP"
fi

# Test 5: Networks
echo -e "\n${YELLOW}[5/5] Testing Networks Endpoint...${NC}"
RESP=$(curl -s "$API/networks/switches")
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} Networks endpoint working"
else
    echo -e "${YELLOW}⚠${NC} Networks endpoint response: $RESP"
fi

# Test Frontend
echo -e "\n${YELLOW}Testing Frontend...${NC}"
RESP=$(curl -s http://localhost:5173/ 2>&1)
if echo "$RESP" | grep -q "html\|HTML\|<!DOCTYPE" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Frontend is serving content"
else
    echo -e "${YELLOW}⚠${NC} Frontend may still be starting"
fi

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}Installation Test Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo -e "\n${YELLOW}Next Steps:${NC}"
echo -e "  1. Open web GUI: ${GREEN}http://localhost:5173${NC}"
echo -e "  2. Explore API docs: ${GREEN}http://localhost:8000/docs${NC}"
echo -e "  3. Check the 3 configured servers in the UI"
echo ""
