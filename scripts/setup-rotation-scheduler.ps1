# Schedule daily API key rotation at 2 AM
# Run as Administrator

$TaskName = "SNAC-v2-Rotate-API-Keys"
$ScriptPath = "s:\snac-v2\snac-v2\scripts\rotate-api-keys.ps1"
$Trigger = New-ScheduledTaskTrigger -Daily -At "2:00 AM"
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File `"$ScriptPath`""
$Settings = New-ScheduledTaskSettingsSet -RunOnlyIfNetworkAvailable -MultipleInstances IgnoreNew

# Check if task already exists
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Write-Host "Task already exists. Updating..." -ForegroundColor Yellow
    Set-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings
    if ($?) {
        Write-Host "✅ Task updated: '$TaskName' at 2:00 AM daily" -ForegroundColor Green
    } else {
        Write-Error "Failed to update scheduled task: $TaskName"
        exit 1
    }
} else {
    Write-Host "Creating new task..." -ForegroundColor Cyan
    Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Auto-rotate SNAC-v2 OpenAI API keys daily at 2 AM"
    if ($?) {
        Write-Host "✅ Task created: '$TaskName' at 2:00 AM daily" -ForegroundColor Green
    } else {
        Write-Error "Failed to create scheduled task: $TaskName"
        exit 1
    }
}

Write-Host "   Script: $ScriptPath" -ForegroundColor DarkGray
Write-Host "   Logs: s:\snac-v2\snac-v2\logs\rotation-audit.log" -ForegroundColor DarkGray
