# SNAC v2 Task Approval - PowerShell Version
# Usage: .\approve-task.ps1 "TASK DESCRIPTION"

param(
    [Parameter(Mandatory=$true)]
    [string]$Task
)

$VPS_IP = "187.77.3.56"
$API_URL = "http://${VPS_IP}:8000"

Write-Host "Sending task to SNAC v2 agent..."
Write-Host "Task: $Task"

try {
    $body = @{
        task = $Task
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$API_URL/agent/run" `
        -Method Post `
        -ContentType "application/json" `
        -Body $body `
        -TimeoutSec 60

    if ($response.status -eq "completed") {
        Write-Host "TASK COMPLETE"
        Write-Host "Result: $($response.final_result)"
    }
    elseif ($response.status -eq "error") {
        Write-Host "TASK ERROR"
        Write-Host "Error: $($response.error)"
    }
    else {
        Write-Host "Status: $($response.status)"
        Write-Host "Response: $($response | ConvertTo-Json -Compress)"
    }
}
catch {
    Write-Host "ERROR: $_"
}
