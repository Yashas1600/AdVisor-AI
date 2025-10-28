#!/bin/bash
# Script to kill and restart the AdVisor API on AWS EC2

EC2_HOST="ec2-user@52.53.159.105"
BACKEND_DIR="~/AdVisor/backend"

echo "🔍 Connecting to EC2 instance..."

# Kill existing API process
echo "🛑 Killing existing API process..."
ssh $EC2_HOST << 'EOF'
  # Find and kill any uvicorn processes on port 8000
  sudo lsof -ti:8000 | xargs -r sudo kill -9

  # Also kill by process name as backup
  pkill -f "uvicorn main:app" || true

  echo "✅ Existing processes terminated"
EOF

# Optional: Pull latest changes
echo "📦 Pulling latest changes from git..."
ssh $EC2_HOST << EOF
  cd $BACKEND_DIR
  git pull origin main
  echo "✅ Git pull complete"
EOF

# Restart the API
echo "🚀 Starting API server..."
ssh $EC2_HOST << EOF
  cd $BACKEND_DIR
  nohup uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/advisor_api.log 2>&1 &
  echo "✅ API server started in background"

  # Wait a moment and check if it's running
  sleep 3
  if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ API is listening on port 8000"
    echo "📋 Logs: tail -f /tmp/advisor_api.log"
  else
    echo "❌ API failed to start, check logs: cat /tmp/advisor_api.log"
  fi
EOF

echo ""
echo "🎉 Done! API should be running at http://52.53.159.105:8000"
echo "🔍 Test it: curl http://52.53.159.105:8000/agents/personas"
