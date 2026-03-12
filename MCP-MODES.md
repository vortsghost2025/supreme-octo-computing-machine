# MCP Modes (Stable vs Hostinger)

Use this to avoid Kilo disconnect loops from Hostinger MCP restarts.

## Files
- `.vscode/mcp.local.json`: Safe local profile (filesystem only)
- `.vscode/mcp.hostinger.template.json`: Template for your Hostinger profile
- `.vscode/mcp.vps.json`: VPS-only profile (no local filesystem MCP server)
- `.vscode/mcp.json`: Active profile used by the extension

## Switch to Local (recommended default)
```powershell
./set-mcp-local.ps1
```
Then reload VS Code window.

## Switch to VPS-only (no local MCP processes)
```powershell
./set-mcp-vps.ps1
```
Then reload VS Code window.

## Switch to Hostinger profile
1. Copy template to real profile:
```powershell
Copy-Item .vscode/mcp.hostinger.template.json .vscode/mcp.hostinger.json
```
2. Edit `.vscode/mcp.hostinger.json` with your real Hostinger MCP command/args.
3. Switch profile:
```powershell
./set-mcp-hostinger.ps1
```
4. Reload VS Code window.

## Important
- Keep Hostinger MCP approval manual (do not use always-allow).
- If disconnect loop starts, switch back immediately with:
```powershell
./set-mcp-local.ps1
```

## Kilo VPS-safe mode (prevents local filesystem MCP respawn)
```powershell
./set-kilo-vps-mode.ps1
```
Then reload VS Code window.
