#!/usr/bin/env bash

# Wave 1 – System health scan
# -------------------------------------------------
# List all Docker containers and their status
ssh root@187.77.3.56 "docker ps -a"

# Capture CPU / memory usage (top snapshot)
ssh root@187.77.3.56 "top -b -n1 | head -20"

# Disk usage
ssh root@187.77.3.56 "df -h"

# Fetch logs for unhealthy containers (kilo-gateway and snac_qdrant)
ssh root@187.77.3.56 "docker logs kilo-gateway --tail 200"
ssh root@187.77.3.56 "docker logs snac_qdrant --tail 200"

# Wave 2 – Small creation: create a test artifact file
ssh root@187.77.3.56 "echo 'Kilo orchestration test artifact' > /tmp/kilo_test_artifact.txt"

# Wave 3 – Ramp‑up: run project unit tests and kilcode
ssh root@187.77.3.56 "cd /opt/snac-v2 && npm test"
ssh root@187.77.3.56 "/opt/snac-v2/kilocode/packages/opencode/kilcode --continue"

# Wave 4 – Full‑scale test
# Restart all agent containers (docker compose) and run a sample dbt MCP workflow
ssh root@187.77.3.56 "cd /opt/snac-v2 && docker compose down && docker compose up -d"
# Wait a bit for services to start (adjust sleep as needed)
sleep 30
# Sample dbt MCP call – list recent job runs (replace <JOB_ID> as needed)
ssh root@187.77.3.56 "curl -s http://localhost:3002/list_jobs_runs?job_id=12345&limit=5"

# End of orchestration script
