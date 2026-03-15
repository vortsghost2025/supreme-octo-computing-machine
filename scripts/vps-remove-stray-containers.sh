#!/usr/bin/env bash
set -euo pipefail

# Remove stray containers from the VPS that are not part of the canonical SNAC stack.
#
# Canonical containers managed by docker-compose.yml are:
#   snac_db, snac_redis, snac_qdrant, snac_backend, snac_frontend,
#   snac_nginx, snac_free_agent
#
# Run on the VPS host (or over SSH):
#   ssh root@187.77.3.56 'bash -s' < scripts/vps-remove-stray-containers.sh
#
# History:
#   snac_free_coding_agent was an OLD orphan container (port 3001) that was
#   deployed manually and never added to docker-compose.yml.  It caused Kilo
#   to crash by giving two simultaneous responses to the MCP client.
#   The replacement canonical container is snac_free_agent, which IS defined
#   in docker-compose.yml and is started with the rest of the stack.

CANONICAL=(
  snac_db
  snac_redis
  snac_qdrant
  snac_backend
  snac_frontend
  snac_nginx
  snac_free_agent
)

PROJECT_DIR="/opt/snac-v2/backend"

echo "=== SNAC stray container cleanup START ==="
date -u '+UTC %Y-%m-%d %H:%M:%S'
echo

echo "[1/4] Canonical containers:"
for name in "${CANONICAL[@]}"; do
  status=$(docker inspect --format '{{.State.Status}}' "$name" 2>/dev/null || echo "not found")
  echo "  $name  =>  $status"
done
echo

echo "[2/4] All running containers:"
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' || true
echo

echo "[3/4] Identifying stray containers (running but not in canonical list)..."
STRAYS=()
while IFS= read -r name; do
  is_canonical=false
  for c in "${CANONICAL[@]}"; do
    if [ "$name" = "$c" ]; then
      is_canonical=true
      break
    fi
  done
  if [ "$is_canonical" = false ]; then
    STRAYS+=("$name")
  fi
done < <(docker ps --format '{{.Names}}')

if [ ${#STRAYS[@]} -eq 0 ]; then
  echo "  No stray containers found. Stack is clean."
else
  echo "  Found ${#STRAYS[@]} stray container(s):"
  for s in "${STRAYS[@]}"; do
    echo "    - $s"
    docker stop "$s"   && echo "      stopped"
    docker rm   "$s"   && echo "      removed"
  done
fi
echo

echo "[4/4] Canonical stack health check..."
if [ -d "$PROJECT_DIR" ]; then
  cd "$PROJECT_DIR"
  docker compose ps || true
else
  echo "Project directory not found: $PROJECT_DIR"
fi
echo

echo "=== SNAC stray container cleanup END ==="
