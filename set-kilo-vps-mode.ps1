$ErrorActionPreference = "Stop"

$settingsPath = "C:\Users\seand\AppData\Roaming\Code\User\globalStorage\kilocode.kilo-code\settings\mcp_settings.json"

if (-not (Test-Path $settingsPath)) {
    Write-Error "Missing Kilo MCP settings file: $settingsPath"
}

$json = Get-Content $settingsPath -Raw | ConvertFrom-Json

if ($json.mcpServers -and $json.mcpServers.filesystem) {
    if (-not $json.mcpServers.filesystem.PSObject.Properties['disabled']) {
        $json.mcpServers.filesystem | Add-Member -NotePropertyName disabled -NotePropertyValue $true
    } else {
        $json.mcpServers.filesystem.disabled = $true
    }
    $json.mcpServers.filesystem.alwaysAllow = @()
}

($json | ConvertTo-Json -Compress -Depth 10) | Set-Content $settingsPath -Encoding UTF8

Write-Host "Kilo MCP profile set to VPS-safe mode (filesystem MCP disabled)."
Write-Host "Reload VS Code window to apply changes."
