$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$source = Join-Path $root ".vscode/mcp.vps.json"
$target = Join-Path $root ".vscode/mcp.json"

if (-not (Test-Path $source)) {
    Write-Error "Missing VPS MCP config: $source"
}

Copy-Item -Path $source -Destination $target -Force
Write-Host "Switched MCP mode to VPS-only (no local filesystem MCP server)."
Write-Host "Now reload VS Code window to apply changes."
