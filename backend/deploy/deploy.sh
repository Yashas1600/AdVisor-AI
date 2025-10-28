#!/bin/bash

# AdVisor AWS Deployment Script
# Run this on your EC2 instance

set -e

echo "=================================="
echo "AdVisor AWS Deployment"
echo "=================================="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then
   echo "Please do not run as root"
   exit 1
fi

# Update system
echo "1. Updating system..."
sudo apt update && sudo apt upgrade -y

# Install Docker
echo "2. Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    echo "✓ Docker installed"
else
    echo "✓ Docker already installed"
fi

# Install Docker Compose
echo "3. Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✓ Docker Compose installed"
else
    echo "✓ Docker Compose already installed"
fi

# Clone repository
echo "4. Setting up application..."
if [ ! -d "AdVisor" ]; then
    git clone https://github.com/s21sharan/AdVisor.git
    cd AdVisor/backend
else
    cd AdVisor/backend
    git pull
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "5. Creating .env file..."
    read -p "Enter FETCH_AI_API_KEY: " fetch_key
    read -p "Enter SUPABASE_URL: " supabase_url
    read -p "Enter SUPABASE_KEY: " supabase_key
    read -p "Enter OPENAI_API_KEY: " openai_key

    cat > .env << EOF
FETCH_AI_API_KEY=$fetch_key
SUPABASE_URL=$supabase_url
SUPABASE_KEY=$supabase_key
OPENAI_API_KEY=$openai_key
EOF
    echo "✓ .env file created"
else
    echo "5. Using existing .env file"
fi

# Build and run with Docker Compose
echo "6. Building and starting application..."
cd deploy
docker-compose down
docker-compose up -d --build

echo ""
echo "=================================="
echo "✓ Deployment Complete!"
echo "=================================="
echo ""
echo "API running at: http://$(curl -s ifconfig.me):8000"
echo ""
echo "Test with:"
echo "  curl http://$(curl -s ifconfig.me):8000/"
echo ""
echo "View logs:"
echo "  docker-compose logs -f"
echo ""
echo "Next steps:"
echo "  1. Test the API endpoints"
echo "  2. Deploy coordinator agent on Agentverse"
echo "  3. Set up Nginx for HTTPS (optional)"
echo ""
