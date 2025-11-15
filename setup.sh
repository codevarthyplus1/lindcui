#!/bin/bash
# Setup script for KVM Cluster Management System

set -e

echo "========================================="
echo "KVM Cluster Management System - Setup"
echo "========================================="

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "Error: This system is designed for Linux"
    exit 1
fi

# Backend setup
echo ""
echo "Setting up backend..."
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
pip install --upgrade pip
pip install -r requirements.txt

# Create config from example if it doesn't exist
if [ ! -f "config.yaml" ]; then
    echo "Creating config.yaml from example..."
    cp config.example.yaml config.yaml
    echo "Please edit backend/config.yaml with your cluster configuration"
fi

# Initialize database
echo "Initializing database..."
python init_db.py

echo "Backend setup complete!"

# Frontend setup
echo ""
echo "Setting up frontend..."
cd ../frontend

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed. Please install Node.js 16+ and try again."
    exit 1
fi

# Install dependencies
echo "Installing Node.js dependencies..."
npm install

echo "Frontend setup complete!"

# Done
cd ..
echo ""
echo "========================================="
echo "Setup complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Edit backend/config.yaml with your cluster configuration"
echo "2. Start the backend:"
echo "   cd backend && source venv/bin/activate && python main.py"
echo "3. Start the frontend (in a new terminal):"
echo "   cd frontend && npm run dev"
echo "4. Access the GUI at http://localhost:3000"
echo ""
echo "For production deployment, see README.md"
echo ""
