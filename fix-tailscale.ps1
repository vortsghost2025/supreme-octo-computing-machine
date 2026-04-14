# Fix Tailscale + Ollama connectivity
# Run this PowerShell as ADMINISTRATOR

Write-Host "=== Fixing Tailscale/Ollama Connection ===" -ForegroundColor cyan

# 1. Enable Tailscale firewall rules
Write-Host "[1/4] Enabling Tailscale firewall..." -ForegroundColor yellow
Set-NetFirewallRule -DisplayGroup "Tailscale" -Enabled True -ErrorAction SilentlyContinue

# 2. Allow port 9001 for Ollama
Write-Host "[2/4] Opening port 9001 for Ollama..." -ForegroundColor yellow
New-NetFirewallRule -DisplayName "Ollama Tailscale" -Direction Inbound -Protocol TCP -LocalPort 9001 -Action Allow -ErrorAction SilentlyContinue

# 3. Check Ollama config
$ollamaConfig = "$env:LOCALAPPDATA\Ollama\ollama.yaml"
if (Test-Path $ollamaConfig) {
    Write-Host "[3/4] Ollama config exists" -ForegroundColor green
} else {
    Write-Host "[3/4] Creating Ollama config..." -ForegroundColor yellow
    "listen: 0.0.0.0:9001" | Out-File -FilePath $ollamaConfig -Encoding utf8
}

# 4. Show status
Write-Host "[4/4] Status:" -ForegroundColor yellow
Write-Host "Tailscale IP: $(tailscale ip -4)" -ForegroundColor cyan
Write-Host "Ollama test: " -NoNewline
try {
    $response = Invoke-WebRequest -Uri "http://localhost:9001/api/tags" -TimeoutSec 3 -ErrorAction SilentlyContinue
    if ($response) { Write-Host "WORKING" -ForegroundColor green }
} catch { Write-Host "not responding locally" -ForegroundColor red }

Write-Host ""
Write-Host "Done! Now test from VPS: curl http://$(tailscale ip -4):9001/api/tags" -ForegroundColor cyan
