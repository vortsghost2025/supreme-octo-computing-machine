# emergency-stop-api.ps1
# ---------------------------------------------------------------------------
# EMERGENCY: Blanks the Anthropic / OpenAI API key stored in Kilo's
# VS Code settings so no more API calls can be made from this machine.
#
# Run this immediately if you have been charged unexpectedly.
# Then go to https://console.anthropic.com and revoke the key there too.
#
# USAGE
#   Open a PowerShell terminal in VS Code (Ctrl+`) and run:
#     ./scripts/emergency-stop-api.ps1
# ---------------------------------------------------------------------------

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$cleared = @()
$skipped = @()

# ── Helper: blank key-like values in a JSON settings file ───────────────────
function Clear-ApiKeysInJsonFile {
    param(
        [string]$FilePath,
        [string[]]$KeyPatterns = @(
            "apiKey", "api_key", "openaiApiKey", "anthropicApiKey",
            "kiloApiKey", "clineApiKey", "openai_api_key",
            "secretKey", "accessKey"
        )
    )

    if (-not (Test-Path $FilePath)) { return $false }

    $raw = Get-Content $FilePath -Raw -Encoding UTF8
    if ([string]::IsNullOrWhiteSpace($raw)) { return $false }

    try {
        $json = $raw | ConvertFrom-Json
    }
    catch {
        Write-Warning "Could not parse $FilePath as JSON — skipping."
        return $false
    }

    $changed = $false

    foreach ($pattern in $KeyPatterns) {
        # Search all properties at any depth using a helper
        $props = $json.PSObject.Properties | Where-Object { $_.Name -match $pattern }
        foreach ($prop in $props) {
            $val = $prop.Value
            if ($val -is [string] -and $val.Length -gt 8) {
                $prop.Value = ""
                $changed = $true
                Write-Host "  Blanked: $($prop.Name) in $(Split-Path $FilePath -Leaf)" -ForegroundColor Yellow
            }
        }
    }

    if ($changed) {
        $json | ConvertTo-Json -Depth 20 | Set-Content $FilePath -Encoding UTF8
    }

    return $changed
}

Write-Host ""
Write-Host "=== API Key Emergency Stop ===" -ForegroundColor Red
Write-Host ""

# ── 1. Kilo Code extension settings (VS Code user globalStorage) ─────────────
$kiloStorageDir = Join-Path $env:APPDATA "Code\User\globalStorage\kilocode.kilo-code\settings"
$kiloSettingsFiles = @(
    (Join-Path $kiloStorageDir "mcp_settings.json"),
    (Join-Path $kiloStorageDir "mcp_settings.snac-only.json")
)

# Also search for any .json in the kilo storage dir
if (Test-Path $kiloStorageDir) {
    $kiloSettingsFiles += Get-ChildItem $kiloStorageDir -Filter "*.json" -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty FullName
    $kiloSettingsFiles = $kiloSettingsFiles | Sort-Object -Unique
}

foreach ($f in $kiloSettingsFiles) {
    $result = Clear-ApiKeysInJsonFile -FilePath $f
    if ($result) { $cleared += $f } else { $skipped += $f }
}

# ── 2. VS Code user settings.json (holds kilocode.* and cline.* settings) ───
$vsCodeSettings = Join-Path $env:APPDATA "Code\User\settings.json"
if (Test-Path $vsCodeSettings) {
    $raw = Get-Content $vsCodeSettings -Raw -Encoding UTF8
    if ($raw) {
        try {
            $json = $raw | ConvertFrom-Json

            # Kilo Code stores API key in settings like "kilo-code.apiKey" or "kilocode.apiKey"
            $keyPaths = @(
                "kilo-code.apiKey",
                "kilocode.apiKey",
                "cline.apiKey",
                "continue.anthropicApiKey",
                "continue.openaiApiKey",
                "openai.apiKey"
            )

            $changed = $false
            foreach ($keyPath in $keyPaths) {
                $parts = $keyPath -split "\."
                if ($parts.Count -eq 2) {
                    $ns = $parts[0]; $prop = $parts[1]
                    if ($json.PSObject.Properties[$ns] -and
                        $json.$ns.PSObject.Properties[$prop]) {
                        $val = $json.$ns.$prop
                        if ($val -is [string] -and $val.Length -gt 8) {
                            $json.$ns.$prop = ""
                            $changed = $true
                            Write-Host "  Blanked: $keyPath in settings.json" -ForegroundColor Yellow
                        }
                    }
                }
            }

            if ($changed) {
                $json | ConvertTo-Json -Depth 20 | Set-Content $vsCodeSettings -Encoding UTF8
                $cleared += $vsCodeSettings
            } else {
                $skipped += $vsCodeSettings
            }
        }
        catch {
            Write-Warning "Could not parse settings.json — skipping: $($_.Exception.Message)"
            $skipped += $vsCodeSettings
        }
    }
}

# ── 3. Local .env file (blanks OPENAI_API_KEY / ANTHROPIC_API_KEY) ───────────
$repoRoot    = Split-Path -Parent $PSScriptRoot
$localEnvFile = Join-Path $repoRoot ".env"

if (Test-Path $localEnvFile) {
    $lines = Get-Content $localEnvFile
    $newLines = @()
    $envChanged = $false

    foreach ($line in $lines) {
        if ($line -match '^(OPENAI_API_KEY|ANTHROPIC_API_KEY|CLAUDE_API_KEY)\s*=\s*\S+') {
            $key = ($line -split '=')[0].Trim()
            $newLines += "$key=REMOVED_BY_EMERGENCY_STOP"
            $envChanged = $true
            Write-Host "  Blanked: $key in .env" -ForegroundColor Yellow
        } else {
            $newLines += $line
        }
    }

    if ($envChanged) {
        Set-Content $localEnvFile -Value $newLines
        $cleared += $localEnvFile
    }
}

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host ""
if ($cleared.Count -gt 0) {
    Write-Host "✅ Blanked API keys in $($cleared.Count) file(s):" -ForegroundColor Green
    $cleared | ForEach-Object { Write-Host "   $_" -ForegroundColor Green }
} else {
    Write-Host "ℹ️  No API keys found in local config files." -ForegroundColor Cyan
    Write-Host "   This may mean the key was only stored inside the Kilo extension UI" -ForegroundColor Cyan
    Write-Host "   and needs to be removed manually (see instructions below)." -ForegroundColor Cyan
}

Write-Host ""
Write-Host "=== NEXT REQUIRED STEPS ===" -ForegroundColor Red
Write-Host ""
Write-Host "1. GO TO https://console.anthropic.com RIGHT NOW" -ForegroundColor White
Write-Host "   → API Keys → Revoke the key Kilo was using" -ForegroundColor White
Write-Host "   → Billing / Usage Limits → Set monthly limit to $10 or less" -ForegroundColor White
Write-Host ""
Write-Host "2. In VS Code: Kilo panel → Settings → API Key field → DELETE the value there" -ForegroundColor White
Write-Host "   (This script clears saved config files; the extension UI stores a copy too)" -ForegroundColor White
Write-Host ""
Write-Host "3. Email support@anthropic.com to dispute the $250 charge." -ForegroundColor White
Write-Host "   Subject: 'Unexpected API charge - requesting refund'" -ForegroundColor White
Write-Host ""
Write-Host "4. Read SPENDING-EMERGENCY.md in this repo for full instructions." -ForegroundColor White
Write-Host ""
