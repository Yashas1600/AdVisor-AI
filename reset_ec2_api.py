#!/usr/bin/env python3
"""
Reset AWS EC2 API - Python Script
Quick script to restart the AdVisor API on AWS EC2
"""

import subprocess
import sys
import time

# EC2 Configuration
EC2_IP = "52.53.159.105"
EC2_USER = "ec2-user"
EC2_KEY_PATH = "~/.ssh/your-ec2-key.pem"  # Update this

def run_ssh_command(command):
    """Run a command on EC2 via SSH"""
    ssh_cmd = [
        "ssh",
        # "-i", EC2_KEY_PATH,  # Uncomment if you need to specify key
        f"{EC2_USER}@{EC2_IP}",
        command
    ]

    try:
        result = subprocess.run(
            ssh_cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return None, "Command timed out", 1
    except Exception as e:
        return None, str(e), 1

def main():
    print("🔄 Resetting AWS EC2 API...")
    print(f"📡 Connecting to {EC2_IP}...")

    # Step 1: Kill existing process
    print("\n1️⃣ Stopping existing API process...")
    stdout, stderr, code = run_ssh_command('pkill -f "uvicorn main:app"')
    if code == 0 or "no process found" in stderr.lower():
        print("   ✓ Existing process stopped")
    else:
        print(f"   ⚠️  Warning: {stderr}")

    # Step 2: Pull latest code
    print("\n2️⃣ Pulling latest code from GitHub...")
    stdout, stderr, code = run_ssh_command('cd ~/AdVisor && git pull origin main')
    if code == 0:
        print("   ✓ Code updated")
        print(f"   {stdout.strip()}")
    else:
        print(f"   ⚠️  Warning: {stderr}")

    # Step 3: Start API
    print("\n3️⃣ Starting API service...")
    start_cmd = 'cd ~/AdVisor/backend && nohup uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/advisor_api.log 2>&1 &'
    stdout, stderr, code = run_ssh_command(start_cmd)
    print("   ✓ API service started")

    # Step 4: Wait and check health
    print("\n4️⃣ Checking API health...")
    time.sleep(3)
    stdout, stderr, code = run_ssh_command('curl -s http://localhost:8000/health')

    if code == 0 and stdout:
        print("   ✅ API is healthy!")
        print(f"   Response: {stdout.strip()}")
    else:
        print("   ❌ API health check failed")
        print("   Checking logs...")
        stdout, stderr, code = run_ssh_command('tail -20 /tmp/advisor_api.log')
        print(f"\n   Last 20 log lines:\n{stdout}")
        return 1

    # Final status
    print("\n" + "="*50)
    print("✅ Deployment complete!")
    print(f"🌐 API URL: http://{EC2_IP}:8000")
    print(f"📊 Health: http://{EC2_IP}:8000/health")
    print(f"📚 Docs: http://{EC2_IP}:8000/docs")
    print(f"🔍 Personas: http://{EC2_IP}:8000/api/personas/all")
    print("="*50)

    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
