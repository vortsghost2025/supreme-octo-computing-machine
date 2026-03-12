param(
    [switch]$Force,
    [switch]$DryRun,
    [switch]$Verbose
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RotationDir = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $RotationDir ".env"
$RotationFile = Join-Path $RotationDir ".env.rotation"
$LogFile = Join-Path $RotationDir "logs\rotation-audit.log"

if (-not (Test-Path $RotationFile)) {
    Write-Error "Rotation config not found: $RotationFile"
    exit 1
}

function Read-RotationConfig {
    $config = @{}
    (Get-Content $RotationFile) | Where-Object { $_ -match '^[^#]*=' } | ForEach-Object {
        $k, $v = $_ -split '=', 2
        $config[$k.Trim()] = $v.Trim()
    }
    return $config
}

function Get-NextKeyIndex {
    param([int]$Current, [int]$Total)
    return ($Current + 1) % $Total
}

function Update-RotationConfig {
    param([hashtable]$Config, [int]$NewIndex, [string]$NewKey)
    
    $lines = @()
    (Get-Content $RotationFile) | ForEach-Object {
        if ($_ -match '^CURRENT_KEY_INDEX=') {
            $lines += "CURRENT_KEY_INDEX=$NewIndex"
        } elseif ($_ -match '^LAST_ROTATION=') {
            $lines += "LAST_ROTATION=$([DateTime]::UtcNow.ToString('o'))"
        } else {
            $lines += $_
        }
    }
    
    Set-Content $RotationFile -Value $lines
}

function Update-EnvFile {
    param([string]$NewKey)
    
    $lines = @()
    (Get-Content $EnvFile) | ForEach-Object {
        if ($_ -match '^OPENAI_API_KEY=') {
            $lines += "OPENAI_API_KEY=$NewKey"
        } else {
            $lines += $_
        }
    }
    
    Set-Content $EnvFile -Value $lines
}

function Write-AuditLog {
    param([string]$Message)
    
    if (-not (Test-Path (Split-Path $LogFile))) {
        New-Item -ItemType Directory -Path (Split-Path $LogFile) -Force | Out-Null
    }
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content $LogFile "$timestamp | $Message"
}

# Main
$config = Read-RotationConfig
$currentIndex = [int]$config['CURRENT_KEY_INDEX']
$totalKeys = 3  # KEY_0, KEY_1, KEY_2

$nextIndex = Get-NextKeyIndex $currentIndex $totalKeys
$nextKeyVar = "KEY_" + $nextIndex
$nextKey = $config[$nextKeyVar]

if (-not $nextKey) {
    Write-Error "Key not found: $nextKeyVar"
    exit 1
}

$oldKeyVar = "KEY_" + $currentIndex

if ($DryRun) {
    Write-Host "DRY RUN: Would rotate $oldKeyVar → $nextKeyVar" -ForegroundColor Yellow
    exit 0
}

try {
    Update-RotationConfig $config $nextIndex $nextKey
    Update-EnvFile $nextKey
    Write-AuditLog "Rotated: $oldKeyVar → $nextKeyVar (index $currentIndex → $nextIndex)"
    Write-Host "✅ Rotation successful: $oldKeyVar → $nextKeyVar" -ForegroundColor Green
} catch {
    Write-Error "Rotation failed: $_"
    Write-AuditLog "FAILED: $_ "
    exit 1
}
