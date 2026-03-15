$ErrorActionPreference = "Stop"

# Use $env:APPDATA so this works for any Windows user, not just C:\Users\seand
$settingsDir = Join-Path $env:APPDATA "Code\User\globalStorage\kilocode.kilo-code\settings"
$source = Join-Path $settingsDir "mcp_settings.snac-only.json"
$target = Join-Path $settingsDir "mcp_settings.json"

if (-not (Test-Path $source)) {
    Write-Error "Missing Kilo SNAC-only profile: $source"
}

Copy-Item -Path $source -Destination $target -Force
Write-Host "Kilo MCP profile set to SNAC-only workspace isolation."
Write-Host "Reload VS Code or restart Kilo to apply the new filesystem scope."
