param(
    [switch]$FailOnError,
    [string]$SshHost = "root@187.77.3.56",
    [string]$VpsComposeDir = "/opt/snac-v2/backend"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$allChecksPassed = $true
$summary = @()

function Add-Result {
    param(
        [string]$Check,
        [bool]$Passed,
        [string]$Detail
    )

    $status = if ($Passed) { "PASS" } else { "FAIL" }
    $script:summary += [pscustomobject]@{
        Check = $Check
        Status = $status
        Detail = $Detail
    }

    if (-not $Passed) {
        $script:allChecksPassed = $false
    }
}

function Run-Quiet {
    param([scriptblock]$Action)

    try {
        $output = & $Action 2>&1 | Out-String
        return @{ Ok = $true; Output = $output.Trim() }
    }
    catch {
        return @{ Ok = $false; Output = $_.Exception.Message }
    }
}

Write-Host "=== SNAC Session Truth Snapshot ===" -ForegroundColor Cyan
Write-Host "UTC: $([DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ"))"
Write-Host "Repo: $repoRoot"
Write-Host ""

# 1) Git commit identity
$git = Run-Quiet { git -C $repoRoot rev-parse --short HEAD }
Add-Result -Check "Git commit" -Passed $git.Ok -Detail ($git.Output -replace "`r|`n", " ")

# 2) Rotation scheduler status
$task = Run-Quiet { Get-ScheduledTask -TaskName "SNAC-v2-Rotate-API-Keys" | Select-Object -ExpandProperty State }
Add-Result -Check "Key rotation task" -Passed $task.Ok -Detail ($task.Output -replace "`r|`n", " ")

# 3) Secret files present locally
$envPath = Join-Path $repoRoot ".env"
$rotationPath = Join-Path $repoRoot ".env.rotation"
$hasEnv = Test-Path $envPath
$hasRotation = Test-Path $rotationPath
Add-Result -Check ".env present" -Passed $hasEnv -Detail $envPath
Add-Result -Check ".env.rotation present" -Passed $hasRotation -Detail $rotationPath

# 4) VPS compose status
$composeStatus = Run-Quiet { ssh $SshHost "cd $VpsComposeDir; docker compose ps" }
Add-Result -Check "VPS compose" -Passed $composeStatus.Ok -Detail (($composeStatus.Output -split "`n")[0] -replace "`r", "")

# 5) VPS backend health
$health = Run-Quiet { ssh $SshHost "curl -fsS http://localhost:8000/health" }
Add-Result -Check "VPS backend health" -Passed $health.Ok -Detail (($health.Output -replace "`r|`n", " "))

# Output summary table
$summary | Format-Table -AutoSize

# Save snapshot for next agent/session
$logsDir = Join-Path $repoRoot "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
}

$snapshotFile = Join-Path $logsDir "session-truth-latest.txt"
$snapshotLines = @()
$snapshotLines += "SNAC Session Truth Snapshot"
$snapshotLines += "UTC=$([DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ"))"
$snapshotLines += "REPO=$repoRoot"
$snapshotLines += "SSH_HOST=$SshHost"
$snapshotLines += "VPS_COMPOSE_DIR=$VpsComposeDir"
$snapshotLines += ""
foreach ($row in $summary) {
    $snapshotLines += ("{0} | {1} | {2}" -f $row.Status, $row.Check, $row.Detail)
}
Set-Content -Path $snapshotFile -Value $snapshotLines

Write-Host ""
Write-Host "Snapshot written: $snapshotFile" -ForegroundColor DarkGray

if ($allChecksPassed) {
    Write-Host "SAFE TO PROCEED: VPS truth verified. Do not run local docker compose." -ForegroundColor Green
    exit 0
}

Write-Host "STOP: One or more checks failed. Fix environment/state before implementation." -ForegroundColor Red
if ($FailOnError) {
    exit 1
}

exit 0
