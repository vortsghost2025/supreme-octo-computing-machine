$ErrorActionPreference = "Stop"

$targets = @(
    "C:\Users\seand",
    "S:\snac-v2",
    "S:\workspace",
    "S:\agents",
    "S:\FreeAgent",
    "S:\MYREPOFREEAGENT"
)

Write-Host "=== MACHINE LAYOUT AUDIT ==="

foreach ($target in $targets) {
    if (Test-Path $target) {
        Write-Host "`n[$target]"
        Get-ChildItem -Force $target -ErrorAction SilentlyContinue |
            Select-Object Name, Mode, Length |
            Format-Table -AutoSize |
            Out-String -Width 220 |
            Write-Host
    }
}

Write-Host "`n=== GIT ROOT CHECKS ==="

$gitTargets = @(
    "S:\",
    "S:\snac-v2",
    "S:\snac-v2\snac-v2",
    "S:\workspace"
)

foreach ($target in $gitTargets) {
    if (Test-Path $target) {
        Write-Host "`n[$target]"
        try {
            git -C $target rev-parse --show-toplevel 2>$null | Write-Host
        } catch {
            Write-Host "Not a git worktree"
        }
    }
}

Write-Host "`n=== DUPLICATE PROJECT SIGNALS ==="

$patterns = @("package.json", "docker-compose.yml", "docker-compose-expanded.yml", "main.py", "server.js")

foreach ($pattern in $patterns) {
    Write-Host "`nPattern: $pattern"
    Get-ChildItem -Path "S:\" -Recurse -File -Filter $pattern -ErrorAction SilentlyContinue |
        Select-Object -First 80 FullName |
        Format-Table -AutoSize |
        Out-String -Width 220 |
        Write-Host
}