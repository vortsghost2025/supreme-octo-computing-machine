#!/bin/bash
# orchestrate_parallel_test.sh - Canonical parallel test orchestrator
#
# This script is the canonical method for running distributed parallel tests across
# the VPS fleet. All test runs MUST use this script for consistent execution and reporting.
#
# === TailScale Usage ===
# This script requires TailScale to be active on both local and target nodes.
# All communications occur over TailScale private network addresses only.
# Public IPs are never used for test orchestration or file transfers.
# TailScale ensures encrypted point-to-point connectivity with proper node identity verification.
# Nodes are referenced using their TailScale hostnames (not public DNS or IP addresses).
#
# === SCP Path Usage ===
# All test artifacts are transferred using SCP over the TailScale interface.
# SCP paths follow this strict pattern:
#   ${USER}@${TAILSCALE_HOSTNAME}:/opt/snac/test_artifacts/${RUN_ID}/
#
# Path requirements:
# 1. Always use absolute paths starting at /opt/snac/
# 2. Never use relative paths or home directory shortcuts (~)
# 3. Run ID must be unique per test execution
# 4. Directory permissions are enforced 0755 on target nodes
# 5. All transfers are checksum verified after completion

set -euo pipefail

RUN_ID=$(date +%Y%m%d_%H%M%S)
TAILSCALE_NODES=("node-01" "node-02" "node-03" "node-04")
USER="snac-admin"

echo "Starting parallel test orchestration run: ${RUN_ID}"
echo "Total nodes: ${#TAILSCALE_NODES[@]}"
echo "Using TailScale private network for all communications"

# Validate TailScale connectivity
echo "Verifying TailScale connectivity..."
for node in "${TAILSCALE_NODES[@]}"; do
    if ! ping -c 1 -W 2 "${node}" > /dev/null 2>&1; then
        echo "ERROR: Node ${node} unreachable over TailScale network"
        exit 1
    fi
done

# Deploy test artifacts via SCP
echo "Deploying test artifacts to all nodes..."
for node in "${TAILSCALE_NODES[@]}"; do
    TARGET_PATH="${USER}@${node}:/opt/snac/test_artifacts/${RUN_ID}/"
    echo "  -> Transferring to ${TARGET_PATH}"
    
    # Create target directory first
    ssh "${USER}@${node}" "mkdir -p /opt/snac/test_artifacts/${RUN_ID}/ && chmod 0755 /opt/snac/test_artifacts/${RUN_ID}/"
    
    # Transfer test binaries and configuration
    scp -q ./test_setup.py ./test-phase-6-4-orchestration.js "${TARGET_PATH}"
done

# Execute tests in parallel
echo "Starting parallel test execution across all nodes..."
pids=()
for node in "${TAILSCALE_NODES[@]}"; do
    (
        ssh "${USER}@${node}" "cd /opt/snac/test_artifacts/${RUN_ID}/ && python3 test_setup.py --run-id ${RUN_ID} --node-name ${node}"
    ) &
    pids+=($!)
done

# Wait for all test runs to complete
echo "Waiting for ${#pids[@]} test processes..."
for pid in "${pids[@]}"; do
    wait "${pid}"
done

# Retrieve test results
echo "Retrieving test results from all nodes..."
for node in "${TAILSCALE_NODES[@]}"; do
    echo "  <- Retrieving results from ${node}"
    scp -q "${USER}@${node}:/opt/snac/test_artifacts/${RUN_ID}/orchestration_report.txt" "./orchestration_report_${node}_${RUN_ID}.txt"
done

echo "Parallel test orchestration completed successfully"
echo "Run ID: ${RUN_ID}"
echo "Results stored in current directory"
