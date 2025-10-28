# AWS Deployment Guide - AdVisor Persona Agents

## Architecture Overview

```
User/Agent → Agentverse Coordinator Agent
                    ↓
            AWS EC2 Instance (FastAPI)
                    ↓
        932 Persona Agents (Fetch.ai ASI:One)
                    ↓
            Supabase Database
```

## Prerequisites

1. **AWS Account** with EC2 access
2. **Domain/IP** for your EC2 instance
3. **Environment Variables**:
   - `FETCH_AI_API_KEY`
   - `AGENTVERSE_API_KEY`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `OPENAI_API_KEY`

## Step 1: Launch AWS EC2 Instance

### Recommended Configuration:
- **Instance Type**: `t3.medium` or `t3.large`
- **OS**: Ubuntu 22.04 LTS
- **Storage**: 20 GB SSD
- **Security Group**: Allow ports 22 (SSH), 80 (HTTP), 443 (HTTPS), 8000 (FastAPI)

### Launch Instance:
```bash
# Via AWS Console or CLI
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name your-key-pair \
  --security-group-ids sg-xxxxxxxx \
  --subnet-id subnet-xxxxxxxx
```

## Step 2: Connect to EC2 Instance

```bash
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

## Step 3: Install Dependencies on EC2

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

## Step 4: Deploy Application

### Option A: Using Docker Compose (Recommended)

```bash
# Clone repository or copy files
git clone https://github.com/s21sharan/AdVisor.git
cd AdVisor/backend

# Create .env file
cat > .env << EOF
FETCH_AI_API_KEY=sk_8647c64a7ec3493db51369190475ca12177db5485b9a41f19b0d3256dd5e4366
SUPABASE_URL=https://ltsnoprnomhaoilufuhb.supabase.co
SUPABASE_KEY=your_supabase_key
OPENAI_API_KEY=your_openai_key
EOF

# Build and run
cd deploy
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Option B: Direct Python Deployment

```bash
# Install Python 3.12
sudo apt install python3.12 python3.12-venv python3-pip -y

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run with systemd (production)
sudo nano /etc/systemd/system/advisor-api.service
```

**Service file content:**
```ini
[Unit]
Description=AdVisor FastAPI Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/AdVisor/backend
Environment="PATH=/home/ubuntu/AdVisor/backend/venv/bin"
EnvironmentFile=/home/ubuntu/AdVisor/backend/.env
ExecStart=/home/ubuntu/AdVisor/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Start service
sudo systemctl daemon-reload
sudo systemctl start advisor-api
sudo systemctl enable advisor-api
sudo systemctl status advisor-api
```

## Step 5: Configure Nginx (Optional - for HTTPS)

```bash
# Install Nginx
sudo apt install nginx -y

# Configure reverse proxy
sudo nano /etc/nginx/sites-available/advisor
```

**Nginx config:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/advisor /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Optional: Install SSL certificate
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d your-domain.com
```

## Step 6: Deploy Coordinator Agent on Agentverse

### Local Setup (for testing):
```bash
# Run coordinator locally
cd /Users/sharans/Desktop/projects/AdVisor/backend
export AWS_API_URL="http://your-ec2-public-ip:8000"
python agents/coordinator_agent.py
```

### Agentverse Hosted (production):
1. Go to https://agentverse.ai
2. Create new agent: "AdVisor Coordinator"
3. Copy code from `agents/coordinator_agent.py`
4. Set environment variable: `AWS_API_URL=http://your-ec2-ip:8000`
5. Deploy agent

## Step 7: Test Deployment

```bash
# Test FastAPI on AWS
curl http://your-ec2-ip:8000/

# Test persona agents
curl http://your-ec2-ip:8000/agents/personas

# Test ad analysis
curl -X POST http://your-ec2-ip:8000/agents/analyze-ad-multi \
  -H "Content-Type: application/json" \
  -d '{
    "ad_description": "New fitness app for busy professionals",
    "num_personas": 5
  }'
```

## Step 8: Monitor & Maintain

```bash
# View logs (Docker)
docker-compose logs -f

# View logs (systemd)
sudo journalctl -u advisor-api -f

# Restart service
sudo systemctl restart advisor-api

# Check resource usage
htop
df -h
```

## Security Checklist

- [ ] Change default SSH port
- [ ] Configure firewall (UFW)
- [ ] Set up fail2ban
- [ ] Use HTTPS/SSL certificates
- [ ] Rotate API keys regularly
- [ ] Enable CloudWatch monitoring
- [ ] Set up automated backups
- [ ] Use AWS Secrets Manager for sensitive data

## Cost Estimate

- **EC2 t3.medium**: ~$30/month
- **Data Transfer**: ~$10/month
- **Total**: ~$40/month

## Troubleshooting

### API not responding:
```bash
# Check if service is running
sudo systemctl status advisor-api

# Check port
sudo netstat -tulpn | grep 8000

# Check logs
journalctl -u advisor-api --no-pager | tail -50
```

### Out of memory:
```bash
# Check memory
free -h

# Upgrade instance or add swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## Next Steps

After deployment:
1. Register coordinator agent on Agentverse
2. Test end-to-end communication
3. Set up monitoring and alerts
4. Configure auto-scaling (optional)
5. Implement rate limiting
6. Add API authentication

## Support

For issues, check:
- AWS CloudWatch logs
- FastAPI logs
- Agentverse agent dashboard
- GitHub Issues: https://github.com/s21sharan/AdVisor/issues
