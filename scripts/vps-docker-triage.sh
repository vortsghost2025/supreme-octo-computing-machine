#!/usr/bin/env bash
set -euo pipefail

# Non-destructive VPS triage for SNAC runtime issues.
# Run on the VPS host (or over SSH):
#   ssh root@187.77.3.56 'bash -s' < scripts/vps-docker-triage.sh

PROJECT_DIR="/opt/agent-system"

echo "=== SNAC VPS TRIAGE START ==="
date -u '+UTC %Y-%m-%d %H:%M:%S'
echo

echo "[1/8] Host load and memory"
uptime || true
free -h || true
df -h || true
echo

echo "[2/8] Docker daemon status"
systemctl is-active docker || true
systemctl --no-pager --full status docker | sed -n '1,20p' || true
echo

echo "[3/8] Compose service state"
if [ -d "$PROJECT_DIR" ]; then
  cd "$PROJECT_DIR"
  docker compose ps || true
else
  echo "Project directory not found: $PROJECT_DIR"
fi
echo

echo "[4/8] Recent container exits and restart loops"
docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' || true
echo

echo "[5/8] API and frontend health probes"
curl -fsS http://localhost:8000/health || echo "Backend health probe failed"
curl -fsS http://localhost:3000 || echo "Frontend probe failed"
echo

echo "[6/8] Last 200 lines of compose logs (tail)"
if [ -d "$PROJECT_DIR" ]; then
  cd "$PROJECT_DIR"
  docker compose logs --tail=200 || true
fi
echo

echo "[7/8] OOM / kernel pressure signals"
dmesg -T 2>/dev/null | grep -Ei 'out of memory|killed process|oom' | tail -n 20 || true
journalctl -u docker --since '2 hours ago' --no-pager | tail -n 120 || true
echo

echo "[8/8] Suggested recovery order (manual)"
echo "1) docker compose up -d postgres redis qdrant"
echo "2) docker compose up -d backend cockpit"
echo "3) curl -fsS http://localhost:8000/health"
echo "4) only then evaluate nginx/n8n state"
echo

echo "=== SNAC VPS TRIAGE END ==="
