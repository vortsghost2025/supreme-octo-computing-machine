# Kilo Isolation Notes

This repo uses two Kilo MCP scope modes at the user-settings layer.

## Active intent
Use `SNAC-only` mode while working in this repo to reduce cross-project contamination from `C:\Users\seand`.

## Toggle scripts
- `./set-kilo-snac-mode.ps1` sets Kilo filesystem MCP scope to `S:\snac-v2\snac-v2`
- `./set-kilo-fullhome-mode.ps1` restores the broader `C:\Users\seand` scope

## Important
- These scripts modify Kilo user settings, not repo code.
- Workspace MCP config in `.vscode/mcp.json` is separate from Kilo's internal MCP settings.
- Hostinger MCP remains disabled in Kilo unless you re-enable it manually.
