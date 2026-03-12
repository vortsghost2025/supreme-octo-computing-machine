#!/bin/bash
# SNAC v2 Unified Setup Script
# Run this ONCE on your VPS to set up everything

set -e

echo "=== SNAC v2 Unified Setup ==="

# 1. Stop old projects
echo "[1/5] Stopping old projects..."
cd /opt/snac-v2
docker compose down 2>/dev/null || true

cd /docker/infrastructure
docker compose down 2>/dev/null || true

cd /docker/automation  
docker compose down 2>/dev/null || true

# 2. Create unified docker-compose
echo "[2/5] Creating unified docker-compose..."
mkdir -p /opt/snac-v2-full
cd /opt/snac-v2-full

cat > docker-compose.yml << 'EOF'
services:
  backend:
    build: ./backend
    container_name: snac_backend
    ports:
      - "8000:8000"
    env_file: ./backend/.env
    depends_on:
      - db

  frontend:
    build: ./frontend
    container_name: snac_frontend
    ports:
      - "3000:80"
    depends_on:
      - backend

  db:
    image: postgres:15
    container_name: snac_db
    environment:
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_USER: snac
      POSTGRES_DB: snac
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    container_name: snac_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  qdrant:
    image: qdrant/qdrant:latest
    container_name: snac_qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage

  nginx:
    image: nginx:alpine
    container_name: snac_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
EOF

# 3. Create nginx.conf
echo "[3/5] Creating nginx.conf..."
cat > nginx.conf << 'EOF'
events { worker_connections 1024; }

http {
  upstream backend { server backend:8000; }
  upstream frontend { server frontend:80; }

  server {
    listen 80;
    server_name _;

    location / {
      proxy_pass http://frontend;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
    }

    location /agent/ {
      proxy_pass http://backend;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
    }
  }
}
EOF

# 4. Copy backend and frontend
echo "[4/5] Copying backend and frontend..."
cp -r /opt/snac-v2/backend ./backend
cp -r /opt/snac-v2/frontend ./frontend 2>/dev/null || cp -r /opt/snac-v2/ui ./frontend 2>/dev/null || true

# 5. Start everything
echo "[5/5] Starting all services..."
docker compose up -d

echo "=== DONE ==="
echo "Services starting. Check with: docker compose ps"
