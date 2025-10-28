#!/bin/bash

# Quick Reset Script for AWS EC2 API
# Use this to quickly restart the API on EC2

EC2_IP="52.53.159.105"
EC2_USER="ec2-user"

echo "🔄 Resetting AWS EC2 API..."

# If you have SSH key configured
# ssh "$EC2_USER@$EC2_IP" << 'ENDSSH'

# If you need to specify the key path
# ssh -i ~/.ssh/your-key.pem "$EC2_USER@$EC2_IP" << 'ENDSSH'

# For now, here are the commands to run manually on EC2:
cat << 'EOF'

📋 MANUAL RESET INSTRUCTIONS
============================

1. SSH into your EC2 instance:
   ssh ec2-user@52.53.159.105

2. Stop the current API:
   pkill -f "uvicorn main:app"
   # OR if using systemd:
   # sudo systemctl stop advisor-api

3. Pull latest code (if using git):
   cd ~/AdVisor
   git pull origin main

4. Restart the API:
   cd ~/AdVisor/backend
   nohup uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/advisor_api.log 2>&1 &

   # OR if using systemd:
   # sudo systemctl restart advisor-api

5. Check if API is running:
   curl http://localhost:8000/health

   # Check logs:
   tail -f /tmp/advisor_api.log

6. Exit SSH:
   exit

7. Test from your local machine:
   curl http://52.53.159.105:8000/health

============================

🚀 QUICK ONE-LINER (copy/paste into EC2):
============================
pkill -f "uvicorn main:app" && cd ~/AdVisor && git pull && cd backend && nohup uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/advisor_api.log 2>&1 & sleep 2 && curl http://localhost:8000/health

EOF
