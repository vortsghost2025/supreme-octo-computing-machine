$ErrorActionPreference = "Stop"

$settingsDir = "C:\Users\seand\AppData\Roaming\Code\User\globalStorage\kilocode.kilo-code\settings"
$source = Join-Path $settingsDir "mcp_settings.full-home.json"
$target = Join-Path $settingsDir "mcp_settings.json"

if (-not (Test-Path $source)) {
    Write-Error "Missing Kilo full-home profile: $source"
}

Copy-Item -Path $source -Destination $target -Force
Write-Host "Kilo MCP profile set to full-home scope."
Write-Host "Reload VS Code or restart Kilo to apply the new filesystem scope."
