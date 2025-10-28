#!/bin/bash

# Deploy AdVisor Backend to AWS EC2
# This script updates the code on EC2 and restarts the API

# EC2 instance details
EC2_IP="52.53.159.105"
EC2_USER="ec2-user"
EC2_KEY_PATH="$HOME/.ssh/your-ec2-key.pem"  # Update this path
PROJECT_DIR="AdVisor/backend"

echo "🚀 Deploying AdVisor Backend to AWS EC2..."

# Step 1: SSH into EC2 and pull latest code
echo "📥 Pulling latest code from GitHub..."
ssh -i "$EC2_KEY_PATH" "$EC2_USER@$EC2_IP" << 'ENDSSH'
    cd ~/AdVisor
    git pull origin main
    echo "✓ Code updated from GitHub"
ENDSSH

# Step 2: Restart the API service
echo "🔄 Restarting API service..."
ssh -i "$EC2_KEY_PATH" "$EC2_USER@$EC2_IP" << 'ENDSSH'
    # Kill existing uvicorn process
    pkill -f "uvicorn main:app" || echo "No existing process found"

    # Start uvicorn in background
    cd ~/AdVisor/backend
    nohup uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/advisor_api.log 2>&1 &

    echo "✓ API service restarted"
    sleep 2

    # Check if service is running
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ API is running successfully!"
    else
        echo "❌ API failed to start. Check logs with: tail -f /tmp/advisor_api.log"
    fi
ENDSSH

echo ""
echo "✅ Deployment complete!"
echo "🌐 API is available at: http://$EC2_IP:8000"
echo "📊 Health check: http://$EC2_IP:8000/health"
echo "📚 API docs: http://$EC2_IP:8000/docs"
