# Kill existing Ollama
Get-Process -Name ollama -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 2

# Write config with correct key
Set-Content -Path "C:\Users\seand\AppData\Local\Ollama\ollama.yaml" -Value "host: 0.0.0.0:9001" -Encoding UTF8

# Start Ollama
Start-Process "C:\Users\seand\AppData\Local\Programs\Ollama\ollama.exe" -ArgumentList "serve"
Start-Sleep 8

# Check ports
Write-Host "Checking ports..."
netstat -ano | findstr "LISTENING" | findstr "9001\|11434"
