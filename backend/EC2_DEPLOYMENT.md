# EC2 Deployment Guide for AdVisor API

## Quick Deploy to EC2

### 1. SSH into your EC2 instance
```bash
ssh -i "your-key.pem" ec2-user@52.53.159.105
```

### 2. Navigate to your project and pull latest code
```bash
cd ~/AdVisor/backend
git pull origin main
```

### 3. Install/Update dependencies
```bash
pip install -r requirements.txt
```

### 4. Set environment variables
```bash
# Edit .env file
nano /Users/sharans/Desktop/projects/AdVisor/.env

# Make sure these are set:
SUPABASE_URL=https://ltsnoprnomhaoilufuhb.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
OPENAI_API_KEY=sk-proj-...
FETCH_AI_API_KEY=sk_8647c64a...
```

### 5. Kill existing process and restart
```bash
# Kill existing uvicorn on port 8000
lsof -ti:8000 | xargs kill -9

# Start the API
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &> api.log &
```

### 6. Test the deployment
```bash
# Run health checks
curl http://52.53.159.105:8000/health
curl http://52.53.159.105:8000/health/smart-selector
curl http://52.53.159.105:8000/health/asi-one
```

## Health Check Endpoints

| Endpoint | Purpose | Tests |
|----------|---------|-------|
| `/health` | Basic API health | Server is running |
| `/health/smart-selector` | Smart selector | Supabase + OpenAI + Selector logic |
| `/health/asi-one` | ASI:One integration | Fetch.ai API connectivity |

## Testing from Local Machine

Run the test script:
```bash
cd /Users/sharans/Desktop/projects/AdVisor/backend
./test_ec2_deployment.sh http://52.53.159.105:8000
```

This will test:
1. ✅ Basic health check
2. ✅ Smart Selector (Supabase + OpenAI)
3. ✅ ASI:One (Fetch.ai)
4. ✅ Persona listing
5. ✅ Root endpoint

## System Architecture

```
Frontend (Vercel)
    ↓
POST /api/analyze-ad-smart
    ↓
EC2 FastAPI (52.53.159.105:8000)
    ├─ Smart Selector (OpenAI + Supabase)
    │   └─ Selects 50 personas (age + 40% industry match)
    ├─ ASI:One Agent Analysis
    │   └─ 50 personas analyze feature vector
    └─ Save Results (Supabase)
```

## Troubleshooting

### Port 8000 already in use
```bash
lsof -ti:8000 | xargs kill -9
```

### View logs
```bash
tail -f ~/AdVisor/backend/api.log
```

### Check if API is running
```bash
ps aux | grep uvicorn
```

### Restart API
```bash
lsof -ti:8000 | xargs kill -9
cd ~/AdVisor/backend
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &> api.log &
```

## Production Tips

### Set up systemd service (auto-restart on reboot)
```bash
sudo nano /etc/systemd/system/advisor-api.service
```

Add:
```ini
[Unit]
Description=AdVisor FastAPI Service
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/AdVisor/backend
Environment="PATH=/usr/local/bin:/usr/bin"
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable advisor-api
sudo systemctl start advisor-api
sudo systemctl status advisor-api
```

### Set up HTTPS (optional)
```bash
sudo yum install nginx certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Current Deployment

- **EC2 IP**: 52.53.159.105
- **Port**: 8000
- **Health Check**: http://52.53.159.105:8000/health
- **API Docs**: http://52.53.159.105:8000/docs
