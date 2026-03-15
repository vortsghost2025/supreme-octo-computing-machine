# reset-kilo-extension.ps1
# ---------------------------------------------------------------------------
# Resets the Kilo VS Code extension to a clean, non-conflicting state.
#
# WHY THIS EXISTS
# ---------------
# After reinstalling Windows and keeping files, Kilo may retain a stale MCP
# settings file that still points at the Hostinger VPS backend. If the VPS
# also has a rogue container running (e.g. snac_free_coding_agent on port
# 3001), Kilo receives responses from TWO agent endpoints simultaneously
# (the expected backend + the stray container). This duplicate-location
# conflict causes Kilo to crash as soon as you send a message.
#
# This script:
#   1. Disables the Hostinger/filesystem MCP servers in Kilo's user settings.
#   2. Sets the active MCP profile to SNAC-only (local filesystem scope).
#   3. Clears Kilo's task-state and conversation cache so no stale session
#      references the old (now-removed) VPS container.
#   4. Prints a checklist of manual steps to verify the fix is complete.
#
# BEFORE RUNNING THIS SCRIPT
# --------------------------
# 1. On the VPS, remove the stray container:
#    ssh root@187.77.3.56 'bash -s' < scripts/vps-remove-stray-containers.sh
# 2. Then run this script on your local Windows machine.
# 3. Reload (not just restart) VS Code: Ctrl+Shift+P → "Reload Window"
# ---------------------------------------------------------------------------

$ErrorActionPreference = "Stop"

$settingsDir  = Join-Path $env:APPDATA "Code\User\globalStorage\kilocode.kilo-code\settings"
$settingsFile = Join-Path $settingsDir "mcp_settings.json"
$snacProfile  = Join-Path $settingsDir "mcp_settings.snac-only.json"

# ── 1. Verify the settings directory exists ──────────────────────────────────
if (-not (Test-Path $settingsDir)) {
    Write-Error "Kilo settings directory not found: $settingsDir`nIs Kilo installed for this Windows user?"
}

Write-Host "`n[1/5] Found Kilo settings directory."

# ── 2. Activate the SNAC-only MCP profile ────────────────────────────────────
if (Test-Path $snacProfile) {
    Copy-Item -Path $snacProfile -Destination $settingsFile -Force
    Write-Host "[2/5] Restored SNAC-only MCP profile → mcp_settings.json"
} else {
    # Profile doesn't exist yet – write a safe empty-servers config.
    @{mcpServers = @{}} | ConvertTo-Json -Depth 5 | Set-Content $settingsFile -Encoding UTF8
    Write-Host "[2/5] SNAC-only profile not found; wrote empty mcpServers config to mcp_settings.json"
    Write-Host "      To recreate it, run: ./set-kilo-snac-mode.ps1 after confirming S:\snac-v2\snac-v2 exists."
}

# ── 3. Hard-disable any MCP server that references the VPS ───────────────────
$raw  = Get-Content $settingsFile -Raw
$json = $raw | ConvertFrom-Json

$vpsKeywords = @("hostinger", "vps", "187.77", "snac_free", "3001")
$changed     = $false

if ($json.mcpServers) {
    foreach ($key in @($json.mcpServers.PSObject.Properties.Name)) {
        $server = $json.mcpServers.$key
        $allText = ($server | ConvertTo-Json -Compress -Depth 5).ToLower()
        $isVPS   = $vpsKeywords | Where-Object { $allText -match $_ }
        if ($isVPS) {
            if (-not $server.PSObject.Properties['disabled']) {
                $server | Add-Member -NotePropertyName disabled -NotePropertyValue $true
            } else {
                $server.disabled = $true
            }
            Write-Host "[3/5] Disabled MCP server '$key' (matched VPS/stray keyword)."
            $changed = $true
        }
    }
}

if (-not $changed) {
    Write-Host "[3/5] No VPS-linked MCP servers found — nothing to disable."
}

($json | ConvertTo-Json -Compress -Depth 10) | Set-Content $settingsFile -Encoding UTF8

# ── 4. Clear Kilo task-state and conversation cache ──────────────────────────
$kiloGlobal   = Join-Path $env:APPDATA "Code\User\globalStorage\kilocode.kilo-code"
$cacheTargets = @(
    (Join-Path $kiloGlobal "tasks"),
    (Join-Path $kiloGlobal "cache")
)

foreach ($dir in $cacheTargets) {
    if (Test-Path $dir) {
        Remove-Item -Path $dir -Recurse -Force
        Write-Host "[4/5] Cleared Kilo cache: $dir"
    }
}
if (-not ($cacheTargets | Where-Object { Test-Path $_ })) {
    Write-Host "[4/5] No Kilo cache directories found to clear (already clean)."
}

# ── 5. Summary and manual steps ──────────────────────────────────────────────
Write-Host @"

[5/5] Reset complete.

NEXT STEPS (do these in order):
  1. In VS Code, press Ctrl+Shift+P and choose "Developer: Reload Window"
  2. Open Kilo panel — it should initialise without errors.
  3. Send a test message. If it still crashes, check:
       a. VPS stray containers:
            ssh root@187.77.3.56 'docker ps --format "{{.Names}}\t{{.Ports}}"'
          Expected: NO snac_free_coding_agent line
       b. Run the VPS cleanup script if still present:
            ssh root@187.77.3.56 'bash -s' < scripts/vps-remove-stray-containers.sh
  4. If the Kilo API provider is set to "Custom / OpenAI Compatible" pointing at the
     VPS host (187.77.3.56), change it back to your OpenAI API key in Kilo settings.

WHY THIS HAPPENED
  A container named snac_free_coding_agent was running on the VPS at port 3001.
  It is not part of the canonical SNAC stack. When Kilo sent a message it received
  responses from two agent endpoints at once (duplicate location), causing the crash.
  Removing that container and clearing the stale MCP reference resolves the conflict.
"@
