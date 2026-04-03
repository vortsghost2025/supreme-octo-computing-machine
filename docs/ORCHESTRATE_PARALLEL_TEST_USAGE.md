# orchestrate_parallel_test.sh Usage Guide

## Canonical Status
`scripts/orchestrate_parallel_test.sh` is the **canonical and only supported method** for running distributed parallel tests across the SNAC fleet. All automated and manual test runs must use this script.

---

## TailScale Network Requirements
This script operates exclusively over the TailScale private mesh network:

1.  **Node Identity**: All test nodes are referenced only by their TailScale hostnames
2.  **Encryption**: All control traffic and file transfers use TailScale end-to-end encryption
3.  **Network Isolation**: No test traffic is sent over public internet interfaces
4.  **Connectivity Check**: The script will fail fast if any node is unreachable over TailScale
5.  **Hostnames Used**: `node-01`, `node-02`, `node-03`, `node-04`

No public IP addresses or DNS names are used for test orchestration.

---

## SCP Path Standard
All file transfers follow a strict enforced path structure:

### Transfer Path Pattern
```
${USER}@${TAILSCALE_HOSTNAME}:/opt/snac/test_artifacts/${RUN_ID}/
```

### Path Requirements
| Rule | Description |
|------|-------------|
| Absolute Paths Only | Always use full paths starting at `/opt/snac/`. Never use relative paths or `~` home directory shortcuts. |
| Run ID Isolation | Each test execution gets a unique timestamp-based Run ID directory |
| Permissions | All test directories are created with `0755` permissions |
| Checksum Verification | All SCP transfers are implicitly verified by TailScale transport |
| Consistent Location | Test artifacts are always stored under `/opt/snac/test_artifacts/` on every node |

---

## Script Execution
```bash
cd /workspace/rigs/35e4e9d2-c8ac-4986-8164-b57d324b09bb
chmod +x scripts/orchestrate_parallel_test.sh
./scripts/orchestrate_parallel_test.sh
```

## Output
- Test results are collected to the working directory with naming pattern `orchestration_report_${NODE}_${RUN_ID}.txt`
- All nodes execute tests in parallel
- Script exits with non-zero code if any node test fails
