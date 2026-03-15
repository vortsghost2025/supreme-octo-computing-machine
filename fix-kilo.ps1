# fix-kilo.ps1
# ---------------------------------------------------------------------------
# ONE-COMMAND FIX for Kilo crashing.
#
# What this does (in order):
#   1. SSHes to the VPS and removes the stray container that causes Kilo to
#      receive duplicate responses and crash.
#   2. Resets Kilo's local settings so it has no stale MCP references.
#   3. Tells you to reload VS Code.
#
# USAGE — open a terminal in VS Code (Ctrl+`) and run:
#
#   ./fix-kilo.ps1
#
# If SSH asks for a password, type your VPS root password.
# If SSH fails completely, see the MANUAL STEPS section at the bottom.
# ---------------------------------------------------------------------------

$ErrorActionPreference = "SilentlyContinue"   # don't abort if SSH isn't set up

$VPS_HOST = "root@187.77.3.56"
$SCRIPT    = (Join-Path $PSScriptRoot "scripts\vps-remove-stray-containers.sh") -replace '\\', '/'

Write-Host ""
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        KILO CRASH FIX — running now          ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── STEP 1: VPS cleanup (this is almost always the root cause) ──────────────
Write-Host "STEP 1/3 — Removing stray container from VPS..." -ForegroundColor Yellow
Write-Host "         (this is what crashes Kilo — a rogue docker container on your server)" -ForegroundColor DarkGray
Write-Host ""

$sshAvailable = $null -ne (Get-Command ssh -ErrorAction SilentlyContinue)

if (-not $sshAvailable) {
    Write-Host "  ⚠  SSH command not found on this PC." -ForegroundColor Red
    Write-Host "     Open PowerShell as Administrator and run:" -ForegroundColor White
    Write-Host "       Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0" -ForegroundColor White
    Write-Host "     Then re-run this script." -ForegroundColor White
    Write-Host ""
} else {
    # Try piping the cleanup script to the VPS over SSH
    $scriptContent = ""
    if (Test-Path $SCRIPT) {
        $scriptContent = Get-Content $SCRIPT -Raw
    }

    if ($scriptContent) {
        Write-Host "  Connecting to $VPS_HOST ..." -ForegroundColor DarkGray
        $sshResult = $scriptContent | ssh -o ConnectTimeout=10 -o BatchMode=no $VPS_HOST "bash -s" 2>&1
        $sshOk = $LASTEXITCODE -eq 0
    } else {
        # Fallback: inline minimal cleanup
        $inlineCmd = @'
CANONICAL="snac_db snac_redis snac_qdrant snac_backend snac_frontend snac_nginx"
echo "Running containers:"
docker ps --format "{{.Names}}" | while read name; do
  ok=false
  for c in $CANONICAL; do [ "$name" = "$c" ] && ok=true && break; done
  if [ "$ok" = "false" ]; then
    echo "  Stopping stray: $name"
    docker stop "$name" && docker rm "$name"
  else
    echo "  OK (canonical): $name"
  fi
done
echo "Done."
'@
        Write-Host "  Connecting to $VPS_HOST ..." -ForegroundColor DarkGray
        $sshResult = $inlineCmd | ssh -o ConnectTimeout=10 -o BatchMode=no $VPS_HOST "bash -s" 2>&1
        $sshOk = $LASTEXITCODE -eq 0
    }

    if ($sshOk) {
        Write-Host "  ✅ VPS cleanup complete." -ForegroundColor Green
        if ($sshResult) { $sshResult | ForEach-Object { Write-Host "     $_" -ForegroundColor DarkGray } }
    } else {
        Write-Host "  ⚠  SSH to VPS failed. Exit code: $LASTEXITCODE" -ForegroundColor Red
        Write-Host ""
        Write-Host "  MANUAL ALTERNATIVE — do this in any terminal:" -ForegroundColor White
        Write-Host "    ssh root@187.77.3.56" -ForegroundColor Cyan
        Write-Host "    docker ps    ← look for anything NOT named snac_db/redis/qdrant/backend/frontend/nginx" -ForegroundColor Cyan
        Write-Host "    docker stop <stray-name> && docker rm <stray-name>" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "  Then continue — the next steps still help even without VPS access." -ForegroundColor DarkGray
    }
}

Write-Host ""

# ── STEP 2: Local Kilo reset ─────────────────────────────────────────────────
Write-Host "STEP 2/3 — Resetting Kilo settings on this PC..." -ForegroundColor Yellow

$resetScript = Join-Path $PSScriptRoot "reset-kilo-extension.ps1"
if (Test-Path $resetScript) {
    & $resetScript
} else {
    # Inline minimal version
    $settingsDir  = Join-Path $env:APPDATA "Code\User\globalStorage\kilocode.kilo-code\settings"
    $settingsFile = Join-Path $settingsDir "mcp_settings.json"

    if (Test-Path $settingsDir) {
        @{mcpServers = @{}} | ConvertTo-Json -Depth 10 | Set-Content $settingsFile -Encoding UTF8
        Write-Host "  ✅ Kilo MCP settings cleared." -ForegroundColor Green
    } else {
        Write-Host "  ℹ  Kilo settings directory not found — already clean or not installed yet." -ForegroundColor DarkGray
    }

    # Clear cache
    $kiloRoot = Join-Path $env:APPDATA "Code\User\globalStorage\kilocode.kilo-code"
    foreach ($sub in @("tasks","cache")) {
        $p = Join-Path $kiloRoot $sub
        if (Test-Path $p) { Remove-Item $p -Recurse -Force; Write-Host "  ✅ Cleared Kilo $sub cache." -ForegroundColor Green }
    }
}

Write-Host ""

# ── STEP 3: Instructions ──────────────────────────────────────────────────────
Write-Host "STEP 3/3 — Reload VS Code now:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Press  Ctrl+Shift+P  then type  Reload Window  then press Enter" -ForegroundColor White
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║  After reloading, open the Kilo panel and send a test message.  ║" -ForegroundColor Green
Write-Host "║  If it still crashes, run:  ./fix-kilo.ps1  again.              ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "WHY THIS HAPPENED" -ForegroundColor DarkGray
Write-Host "  A container called snac_free_coding_agent was running on your VPS" -ForegroundColor DarkGray
Write-Host "  outside the normal stack. When Kilo sent a message, it received" -ForegroundColor DarkGray
Write-Host "  responses from two places at once, which caused the crash." -ForegroundColor DarkGray
Write-Host "  Using @swarm (which spawns 5 agents) made this 5x worse because" -ForegroundColor DarkGray
Write-Host "  all 5 agents hit the duplicate endpoint simultaneously." -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Rule: always deploy the VPS with --remove-orphans to prevent recurrence:" -ForegroundColor DarkGray
Write-Host "  ssh root@187.77.3.56 'cd /opt/snac-v2/backend && docker compose up -d --remove-orphans'" -ForegroundColor DarkGray
Write-Host ""
