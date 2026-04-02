#!/usr/bin/env bash
# =============================================================================
# Qdrant WAL Corruption Fix
# =============================================================================
#
# Problem:
#   The snac_qdrant container becomes unhealthy when Qdrant's Write-Ahead Log
#   (WAL) files become corrupted. This typically happens after an unclean
#   shutdown, disk-full events, or filesystem errors.
#
# Procedure:
#   1. Stop the snac_qdrant container gracefully (if running)
#   2. Locate WAL files in the qdrant_data named volume
#   3. Rename corrupted WAL files to *.corrupt.<timestamp> for recovery
#   4. Restart the Qdrant container
#   5. Poll /health until the service reports healthy
#
# Usage:
#   On VPS host:
#     chmod +x scripts/fix-qdrant-wal.sh
#     ./scripts/fix-qdrant-wal.sh
#
#   Via docker (one-shot, mounting the same volume):
#     docker run --rm -v qdrant_data:/qdrant/storage alpine sh -c \
#       "apk add --no-cache bash curl && bash /dev/stdin" < scripts/fix-qdrant-wal.sh
#
#   Via docker-compose (qdrant-recovery service):
#     docker compose run --rm qdrant-recovery
#
# Idempotency:
#   Safe to run multiple times. If no WAL files exist, reports no-op success.
#   If container is already stopped, skips the stop step.
# =============================================================================
set -euo pipefail

CONTAINER_NAME="snac_qdrant"
QDRANT_STORAGE="/qdrant/storage"
HEALTH_URL="http://localhost:6333/health"
POLL_INTERVAL=3
POLL_TIMEOUT=60
CORRUPTED_COUNT=0
REMOVED_WAL=false

log() {
  echo "[fix-qdrant-wal] $*"
}

log_error() {
  echo "[fix-qdrant-wal] ERROR: $*" >&2
}

# --- Detect run context ---
# When running inside a container (docker compose run), there's no docker CLI.
# Skip container stop/start steps and just clean the WAL files on disk.
IN_CONTAINER=false
if [ ! -S /var/run/docker.sock ]; then
  IN_CONTAINER=true
  log "Running inside container — will only clean WAL files on disk."
  log "You must restart the snac_qdrant container manually after this script."
fi

# --- Step 1: Stop Qdrant container ---
if [ "$IN_CONTAINER" = false ]; then
  log "Step 1: Checking container state..."
  if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${CONTAINER_NAME}$"; then
    log "Stopping ${CONTAINER_NAME}..."
    docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || {
      log_error "Failed to stop ${CONTAINER_NAME}"
      exit 1
    }
    log "Container stopped."
  else
    log "Container ${CONTAINER_NAME} is not running — skipping stop."
  fi
else
  log "Step 1: Skipping container stop (running inside container)."
fi

# --- Step 2: Locate and rename corrupted WAL files ---
log "Step 2: Scanning for WAL files in ${QDRANT_STORAGE}..."

if [ ! -d "$QDRANT_STORAGE" ]; then
  log_error "Storage directory ${QDRANT_STORAGE} does not exist."
  exit 1
fi

TIMESTAMP=$(date +%s)

# Find all WAL files under the qdrant storage directory.
# Qdrant stores WAL at: collections/<collection>/0/segments/<segment>/wal/
while IFS= read -r -d '' wal_dir; do
  if [ -d "$wal_dir" ]; then
    for wal_file in "$wal_dir"/wal-*; do
      [ -f "$wal_file" ] || continue
      corrupt_name="${wal_file}.corrupt.${TIMESTAMP}"
      log "Renaming corrupted WAL: ${wal_file} -> ${corrupt_name}"
      mv "$wal_file" "$corrupt_name"
      CORRUPTED_COUNT=$((CORRUPTED_COUNT + 1))
    done
  fi
done < <(find "$QDRANT_STORAGE" -type d -name "wal" -print0 2>/dev/null)

# Also clean up any stale lock files that may block recovery
while IFS= read -r -d '' lock_file; do
  [ -f "$lock_file" ] || continue
  log "Removing stale lock file: ${lock_file}"
  rm -f "$lock_file"
  CORRUPTED_COUNT=$((CORRUPTED_COUNT + 1))
done < <(find "$QDRANT_STORAGE" -name "*.lock" -print0 2>/dev/null)

if [ "$CORRUPTED_COUNT" -gt 0 ]; then
  log "Renamed/cleaned ${CORRUPTED_COUNT} WAL/lock file(s)."
  REMOVED_WAL=true
else
  log "No WAL files found — nothing to clean."
fi

# --- Step 3: Restart Qdrant and poll health ---
if [ "$IN_CONTAINER" = false ]; then
  log "Step 3: Starting ${CONTAINER_NAME}..."
  docker start "$CONTAINER_NAME" >/dev/null 2>&1 || {
    log_error "Failed to start ${CONTAINER_NAME}"
    exit 1
  }

  log "Polling ${HEALTH_URL} for up to ${POLL_TIMEOUT}s..."
  elapsed=0
  healthy=false
  while [ "$elapsed" -lt "$POLL_TIMEOUT" ]; do
    if curl -fsS --max-time 3 "$HEALTH_URL" >/dev/null 2>&1; then
      healthy=true
      break
    fi
    sleep "$POLL_INTERVAL"
    elapsed=$((elapsed + POLL_INTERVAL))
    log "  Waiting... (${elapsed}s/${POLL_TIMEOUT}s)"
  done

  if [ "$healthy" = true ]; then
    log "SUCCESS: ${CONTAINER_NAME} is healthy after ${elapsed}s."
  else
    log_error "TIMEOUT: ${CONTAINER_NAME} did not become healthy within ${POLL_TIMEOUT}s."
    log_error "Check container logs: docker logs ${CONTAINER_NAME}"
    exit 1
  fi
else
  log "Step 3: Skipping container restart (running inside container)."
  if [ "$REMOVED_WAL" = true ]; then
    log "WAL files were cleaned. Restart the container manually:"
    log "  docker compose restart qdrant"
  fi
fi

# --- Summary ---
log "=== Qdrant WAL fix complete ==="
if [ "$CORRUPTED_COUNT" -eq 0 ]; then
  log "Result: No WAL corruption detected (no-op)."
else
  log "Result: Cleaned ${CORRUPTED_COUNT} file(s). Corrupted WAL renamed with .corrupt.${TIMESTAMP} suffix."
fi
