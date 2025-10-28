#!/bin/bash
# Quick EC2 Restart Script
# Run this ON EC2 after pulling latest code

set -e

echo "🔄 Restarting AdVisor API on EC2..."

# Kill existing process
echo "Stopping existing API..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "No existing process on port 8000"

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --upgrade

# Start API in background
echo "Starting API..."
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &> api.log &

# Wait a bit for startup
sleep 3

# Check if running
if lsof -ti:8000 > /dev/null; then
    echo "✅ API started successfully!"
    echo ""
    echo "📊 Status:"
    ps aux | grep uvicorn | grep -v grep
    echo ""
    echo "🔗 Endpoints:"
    echo "  Health:     http://52.53.159.105:8000/health"
    echo "  Docs:       http://52.53.159.105:8000/docs"
    echo "  Logs:       tail -f ~/AdVisor/backend/api.log"
    echo ""
    echo "🧪 Test it:"
    echo "  curl http://52.53.159.105:8000/health"
else
    echo "❌ Failed to start API"
    echo "Check logs: cat api.log"
    exit 1
fi
