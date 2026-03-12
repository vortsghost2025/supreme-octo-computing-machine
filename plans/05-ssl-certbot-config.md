# Planning Document 5: Nginx SSL with Certbot Auto-Renewal

## Overview

Production-grade SSL configuration with automatic certificate renewal using Certbot.

## Components Added

1. **docker-compose.yml Addition** - Nginx with SSL volumes
2. **nginx.conf (SSL-Optimized)** - Mozilla Intermediate profile, HTTP→HTTPS redirect, WebSocket support
3. **Certbot Bootstrapper Script** - `init-ssl.sh` for initial cert issuance and auto-renewal setup

## Key Features

| Feature | Why It Matters |
|---------|----------------|
| **Mozilla Intermediate SSL Profile** | Balances security/compatibility |
| **HTTP→HTTPS Redirect** | Never serves plaintext after setup |
| **Certbot Webroot Challenge** | Zero-downtime renewal |
| **Auto-Renewal Cron** | Certs renew 30 days before expiry |
| **Staging-First Bootstrapping** | Avoids rate limits during initial setup |
| **Nginx Restart on Renewal** | Zero-delay cert activation |
| **Health Check Bypass** | Monitoring tools get 200 without auth |

## Setup Steps

### 1. Configure Before First Run

```bash
DOMAIN="agent.yourdomain.com"  # ← CHANGE ME TO YOUR DOMAIN
EMAIL="admin@yourdomain.com"   # ← CHANGE ME
```

### 2. Run Initial Setup

```bash
chmod +x init-ssl.sh
./init-ssl.sh  # ← ONLY RUN THIS ONCE TO BOOTSTRAP CERTS
```

### 3. Restart Nginx to Load Certs

```bash
docker compose restart nginx
```

### 4. Validation Commands

```bash
# Confirm certs exist
ls -la certbot/conf/live/agent.yourdomain.com/

# Test HTTPS
curl -I https://localhost  # Should return HTTP/2 200

# Check auto-renewal
crontab -l  # Should see the certbot renew line
```

## Critical Next Steps

1. Point your domain (`agent.yourdomain.com`) to your VPS IP (A record)
2. Update `server_name` in `nginx.conf` to your actual domain
3. Re-run `./init-ssl.sh`
4. Enable cockpit auth if needed
5. **Remove port 80 from firewall** after SSL works:
   ```bash
   sudo ufw deny 80/tcp
   sudo ufw allow 443/tcp
   ```
