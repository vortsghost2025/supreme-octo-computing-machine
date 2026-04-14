# Stop existing Ollama processes
Get-Process -Name "ollama" -ErrorAction SilentlyContinue | Stop-Process -Force

# Wait for cleanup
Start-Sleep -Seconds 3

# Set environment variable
$env:OLLAMA_HOST = "0.0.0.0:9001"

# Start Ollama with network access
Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Minimized

# Wait for startup
Start-Sleep -Seconds 5

# Verify it's running
Write-Host "Ollama started with OLLAMA_HOST=$env:OLLAMA_HOST"
Write-Host ""
Write-Host "Testing connection..."
$response = Invoke-WebRequest -Uri "http://localhost:9001/api/tags" -UseBasicParsing
Write-Host "Status: $($response.StatusCode)"
Write-Host ""
Write-Host "Available models:"
ollama list
