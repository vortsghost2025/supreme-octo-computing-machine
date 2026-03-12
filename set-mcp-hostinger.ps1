$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$source = Join-Path $root ".vscode/mcp.hostinger.json"
$target = Join-Path $root ".vscode/mcp.json"

if (-not (Test-Path $source)) {
    Write-Host "Missing Hostinger MCP config: $source"
    Write-Host "Create .vscode/mcp.hostinger.json first, then run this script again."
    Write-Host "Tip: include filesystem and Hostinger servers, and keep Hostinger approvals manual."
    exit 1
}

Copy-Item -Path $source -Destination $target -Force
Write-Host "Switched MCP mode to HOSTINGER profile."
Write-Host "Now reload VS Code window to apply changes."
