# Planning Document 15: Hostinger VPS Deployment Guide

## Overview

Hostinger VPS-specific deployment guide for SNAC v2 - tailored to their infrastructure.

## Hostinger-Specific Notes

### Requirements
- Memory: ≥1024 MB (1GB) - sufficient
- Swap: Must be enabled (critical for memory safety)
- Ubuntu 22.04 template

### Pre-requisites Steps
1. Enable swap (if shows 0 MB)
2. Verify outbound HTTPS to OpenAI
3. Prep .env with OpenAI key

---

## PHASE 0: HOSTINGER-SPECIFIC PREP

### Step 1: Enable Swap
```bash
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
sudo swapon --show
```

### Step 2: Verify Network
```bash
curl -s https://api.openai.com/v1/models | head -n 1
```

### Step 3: Create .env
```bash
mkdir -p /opt/agent-system && cd /opt/agent-system
cat > .env <<EOF
OPENAI_API_KEY=sk-...
POSTGRES_PASSWORD=agent_secure_password_$(openssl rand -hex 8)
EOF
chmod 600 .env
```

---

## PHASE 1: DOCKER INSTALLATION

### Install Docker CE
```bash
sudo apt-get remove -y docker docker-engine docker.io containerd runc
sudo apt-get install -y ca-certificates curl gnupg lsb-release
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo docker run hello-world
```

---

## PHASE 2: DEPLOY & VERIFY

### Step 1: Start Infrastructure
```bash
docker compose up -d postgres redis qdrant nginx
# Wait for health
docker compose ps
```

### Step 2: Start Agent Stack
```bash
docker compose up -d backend cockpit n8n
# Wait for backend ready
curl -s http://localhost:8000/health
```

### Step 3: First Task
```bash
# Ingest test data
curl -s -X POST http://localhost:8000/ingest -H "Content-Type: text/plain" --data-binary "The capital of Japan is Tokyo."

# Send task
curl -s -X POST http://localhost:8000/agent/run -H "Content-Type: application/json" -d '{"task":"QUERY: What is the capital of Japan? Then CALC: 25 * 4"}'
```

---

## PHASE 3: HARDENING

### Step 1: Enable UFW Firewall
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 5678/tcp
sudo ufw enable
```

### Step 2: Set Up Fail2Ban
```bash
sudo apt-get install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Step 3: OpenAI Budget Guardrail
Set in OpenAI dashboard:
- Monthly budget: $4.50
- Hard limit: ENABLED
- Alert threshold: $4.00

### Step 4: Automatic Security Updates
```bash
sudo apt-get install -y unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

---

## VALIDATION CHECKLIST

| Checkpoint | How to Verify | Success Signal |
|------------|---------------|----------------|
| Swap enabled | `free -h` | Shows Swap: 1.0G |
| Docker CE | `docker --version` | Docker version 24.0.+ |
| Infrastructure | `docker compose ps` | All healthy |
| Backend | `curl localhost:8000/health` | {"status":"ok"} |
| Rate limiting | 25 rapid requests | 429 for 11+ |
| Budget guardrail | OpenAI dashboard | Alerts at $4.00 |
| UFW active | `sudo ufw status` | Status: active |
| Fail2Ban | `sudo fail2ban-client status` | Jail list: sshd |
