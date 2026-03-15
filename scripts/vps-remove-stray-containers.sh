#!/usr/bin/env bash
set -euo pipefail

# Remove stray containers from the VPS that are not part of the canonical SNAC stack.
#
# The canonical containers managed by docker-compose.yml are:
#   snac_db, snac_redis, snac_qdrant, snac_backend, snac_frontend, snac_nginx
#
# Run on the VPS host (or over SSH):
#   ssh root@187.77.3.56 'bash -s' < scripts/vps-remove-stray-containers.sh
#
# What this fixes:
#   snac_free_coding_agent was a container running on port 3001 that is not part of
#   the canonical stack. When the Kilo VS Code extension sends a message it routes
#   through the nginx proxy; the presence of this duplicate service caused Kilo to
#   receive conflicting responses from two agent endpoints (duplicate location crash).
#   Removing it restores a single, well-defined backend endpoint.

CANONICAL=(
  snac_db
  snac_redis
  snac_qdrant
  snac_backend
  snac_frontend
  snac_nginx
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
