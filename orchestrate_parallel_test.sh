#!/usr/bin/env bash
# Parallel health checks for Kilo agents on the VPS (run ON the VPS as root).
set -u

REPORT="/tmp/orchestration_report.txt"
WORKDIR=$(mktemp -d /tmp/kilo_parallel_checks.XXXXXX)
trap 'rm -rf "$WORKDIR"' EXIT

run_check() {
  local id="$1"
  local label="$2"
  shift 2
  local out="$WORKDIR/$(printf '%03d' "$id")_${label//[^a-zA-Z0-9_-]/_}.txt"
  {
    echo "=== $label ==="
    "$@" 2>&1 || echo "[check exited $?]"
    echo ""
  } >"$out" &
}

{
  echo "===== Kilo-Agent Parallel Health Report ====="
  echo "Generated at: $(date -Iseconds 2>/dev/null || date)"
  echo "Host: $(hostname 2>/dev/null || echo unknown)"
  echo ""
} >"$REPORT"

docker ps -a --format '{{.Names}}\t{{.Status}}\t{{.Ports}}' >"$WORKDIR/containers.tsv" || true
{
  echo ">> Container list (name, status, ports)"
  cat "$WORKDIR/containers.tsv"
  echo ""
} >>"$REPORT"

echo ">> Running parallel checks…" | tee -a "$REPORT"

id=0
run_check $((++id)) "CPU / MEM snapshot" sh -c 'top -b -n1 2>/dev/null | head -20'
run_check $((++id)) "Disk usage" df -h
if command -v tailscale >/dev/null 2>&1; then
  run_check $((++id)) "TailScale status" tailscale status
else
  run_check $((++id)) "TailScale status" sh -c 'echo "tailscale not installed on VPS"'
fi
run_check $((++id)) "dbt-MCP /list_jobs_runs (sample)" sh -c 'curl -sS --max-time 15 "http://127.0.0.1:3002/list_jobs_runs?limit=5" || true'

for C in kilo-gateway snac_qdrant; do
  if docker ps -a --format '{{.Names}}' | grep -qx "$C"; then
    run_check $((++id)) "${C} logs (last 200 lines)" docker logs "$C" --tail 200
  else
    run_check $((++id)) "${C} logs (last 200 lines)" sh -c "echo \"container $C not found\""
  fi
done

while IFS=$'\t' read -r name status _ports || [[ -n "${name:-}" ]]; do
  [[ -z "${name:-}" ]] && continue
  if [[ "$status" == Up* ]]; then
    run_check $((++id)) "Container ${name} health (container up)" sh -c "echo \"Container $name is UP ($status)\""
  else
    run_check $((++id)) "Container ${name} health (container NOT up)" sh -c "echo \"Container $name — $status\""
  fi
done <"$WORKDIR/containers.tsv"

wait

{
  echo ""
  echo ">> Check outputs (parallel workers)"
  echo ""
  find "$WORKDIR" -maxdepth 1 -type f -name '[0-9][0-9][0-9]_*.txt' | sort | while read -r f; do
    cat "$f"
  done
  echo ">> Small artifact creation"
  echo "Kilo parallel health test artifact – $(date -Iseconds 2>/dev/null || date)" >/tmp/kilo_parallel_test_artifact.txt
  echo "Artifact created at /tmp/kilo_parallel_test_artifact.txt"
  echo ""
} >>"$REPORT"

if [[ -d /opt/snac-v2 ]]; then
  {
    echo ">> npm test (/opt/snac-v2) — sequential, may be slow"
    (cd /opt/snac-v2 && npm test) 2>&1
  } >>"$REPORT" || echo "[npm test failed]" >>"$REPORT"
else
  echo ">> /opt/snac-v2 not found — skipping npm test" >>"$REPORT"
fi

echo "" >>"$REPORT"
echo "===== END OF REPORT =====" >>"$REPORT"

echo "=== Done ==="
echo "Report: $REPORT"
echo "Copy down: scp root@HOST:$REPORT ."
