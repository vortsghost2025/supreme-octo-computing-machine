# SNAC v2 TTS Proxy - PowerShell Version
# Listens to WebSocket and speaks events using Windows Speech Synthesis
# Usage: .\tts-proxy.ps1

Add-Type -AssemblyName System.Speech

$VPS_IP = "187.77.3.56"
$WS_URL = "ws://${VPS_IP}:3000/ws/chat"

$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Rate = 1  # -10 to 10, 0 is normal
$synth.Volume = 100

function Speak {
    param([string]$text)
    $synth.Speak($text)
}

Write-Host "Starting TTS Proxy for SNAC v2..."
Write-Host "Listening to: $WS_URL"
Write-Host "Press Ctrl+C to stop"

Speak "TTS proxy started. Listening for agent events."

$prevStatus = ""
$prevToolCount = 0

# Note: PowerShell doesn't have built-in WebSocket client
# This requires .NET or a package. For now, we'll use a simple HTTP poll approach

# Alternative: Poll the agent status endpoint
$apiUrl = "http://${VPS_IP}:8000"

Write-Host "Using HTTP polling mode (WebSocket client not available in basic PowerShell)"

while ($true) {
    try {
        # Check agent health/status
        $health = Invoke-RestMethod -Uri "$apiUrl/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
        
        if ($health) {
            # Check for any active tasks or status changes
            # You can customize what events to listen for based on your API
            
            # Example: Check for recent completions
            # This would need to be customized based on your actual API response
        }
        
        Start-Sleep -Seconds 5
    }
    catch {
        Write-Host "Connection issue: $_"
        Speak "Connection problem. Retrying..."
        Start-Sleep -Seconds 5
    }
}

# Note: For true WebSocket support in PowerShell, you'd need:
# Install-Module -Name PoshWebSocket -Force
# Or use .NET HttpClient with WebSocketHandler
