param(
    [switch]$Cleanup,
    [int]$Top = 12,
    [switch]$IncludeDocker,
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "SilentlyContinue"

function Get-MemorySummary {
    $os = Get-CimInstance Win32_OperatingSystem
    if (-not $os) { return $null }

    $totalGb = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
    $freeGb = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
    $usedGb = [math]::Round($totalGb - $freeGb, 2)
    $usedPct = if ($totalGb -gt 0) { [math]::Round(($usedGb / $totalGb) * 100, 1) } else { 0 }

    [pscustomobject]@{
        TotalGB = $totalGb
        UsedGB = $usedGb
        FreeGB = $freeGb
        UsedPercent = $usedPct
    }
}

function Get-TopMemoryProcesses {
    Get-Process |
        Sort-Object -Property WorkingSet64 -Descending |
        Select-Object -First $Top |
        ForEach-Object {
            [pscustomobject]@{
                Name = $_.ProcessName
                PID = $_.Id
                MemoryMB = [math]::Round($_.WorkingSet64 / 1MB, 1)
                CPUSeconds = [math]::Round($_.CPU, 1)
            }
        }
}

function Get-ListeningDevProcesses {
    $patterns = @(
        'npm run dev',
        'npm start',
        'vite',
        'next dev',
        'next start',
        'node ',
        'uvicorn',
        'python -m http.server',
        'flask run',
        'gunicorn',
        'dotnet run'
    )

    $conns = Get-NetTCPConnection -State Listen
    $rows = @()

    foreach ($conn in $conns) {
        $pidValue = $conn.OwningProcess
        if (-not $pidValue) { continue }

        $proc = Get-CimInstance Win32_Process -Filter "ProcessId = $pidValue"
        if (-not $proc) { continue }

        $cmd = ($proc.CommandLine | Out-String).Trim()
        $name = $proc.Name

        $isDevMatch = $false
        foreach ($pattern in $patterns) {
            if ($cmd -match [regex]::Escape($pattern) -or $name -match [regex]::Escape($pattern)) {
                $isDevMatch = $true
                break
            }
        }

        if (-not $isDevMatch) { continue }
        if (-not $IncludeDocker -and ($name -match 'docker' -or $cmd -match 'docker')) { continue }

        $rows += [pscustomobject]@{
            Port = $conn.LocalPort
            Address = $conn.LocalAddress
            PID = [int]$pidValue
            Name = $name
            CommandLine = $cmd
        }
    }

    $rows |
        Sort-Object -Property Port, PID -Unique
}

function Stop-DevProcesses {
    param(
        [Parameter(Mandatory = $true)]
        [array]$Targets,
        [switch]$Force
    )

    $stopped = @()

    foreach ($target in $Targets) {
        if (-not $Force) {
            Write-Host "Skip PID $($target.PID) ($($target.Name)) on port $($target.Port). Use -Force to stop." -ForegroundColor Yellow
            continue
        }

        try {
            Stop-Process -Id $target.PID -Force -ErrorAction Stop
            $stopped += $target
            Write-Host "Stopped PID $($target.PID) ($($target.Name)) on port $($target.Port)" -ForegroundColor Green
        }
        catch {
            Write-Host "Failed to stop PID $($target.PID): $($_.Exception.Message)" -ForegroundColor Red
        }
    }

    return $stopped
}

Write-Host "=== Resource Hygiene Report ===" -ForegroundColor Cyan

$summary = Get-MemorySummary
if ($summary) {
    Write-Host "Memory Used: $($summary.UsedGB) GB / $($summary.TotalGB) GB ($($summary.UsedPercent)%)" -ForegroundColor White
}

Write-Host ""
Write-Host "Top Memory Processes" -ForegroundColor Cyan
Get-TopMemoryProcesses | Format-Table -AutoSize

Write-Host ""
Write-Host "Listening Dev Processes" -ForegroundColor Cyan
$dev = Get-ListeningDevProcesses
if (-not $dev -or $dev.Count -eq 0) {
    Write-Host "No obvious local dev servers detected." -ForegroundColor DarkGray
}
else {
    $dev | Select-Object Port, PID, Name, Address | Format-Table -AutoSize
}

if ($Cleanup) {
    Write-Host ""
    Write-Host "Cleanup Mode: enabled" -ForegroundColor Cyan
    $stopped = Stop-DevProcesses -Targets $dev -Force:$Force
    Write-Host "Stopped $($stopped.Count) process(es)." -ForegroundColor Green
}
else {
    Write-Host ""
    Write-Host "Cleanup Mode: disabled (run with -Cleanup -Force to stop detected dev servers)." -ForegroundColor DarkYellow
}
