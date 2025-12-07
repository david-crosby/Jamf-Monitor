#!/bin/bash

set -e

echo "Jamf Monitor - Setup Script"
echo "=============================="
echo ""

if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed"
    exit 1
fi

echo "Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing backend dependencies..."
pip install --upgrade pip
pip install --break-system-packages -r requirements.txt

if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "Please edit backend/.env with your Jamf Pro credentials"
    echo "Generate a secret key with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
fi

cd ..

echo ""
echo "Setting up frontend..."
cd frontend

echo "Installing frontend dependencies..."
npm install

if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
fi

cd ..

echo ""
echo "=============================="
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit backend/.env with your Jamf Pro credentials"
echo "2. Start the backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "3. Start the frontend: cd frontend && npm run dev"
echo ""
echo "Default login credentials:"
echo "Username: admin"
echo "Password: changeme"
