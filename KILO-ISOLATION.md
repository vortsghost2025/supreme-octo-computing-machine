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

## VPS stray containers — known crash trigger

If Kilo crashes as soon as you send a message, even after reinstalling VS Code or
resetting Windows, the cause is almost always a **stray container on the VPS** that
creates a duplicate agent endpoint.

The specific container that caused this problem: **`snac_free_coding_agent`** (port 3001)
on the Hostinger VPS. It is **not** part of the canonical SNAC stack and should not exist.

When Kilo connects to the backend and this container is also running, Kilo receives
conflicting responses from two locations simultaneously and crashes.

### Fix (two steps, in order)

**Step 1 — Remove the stray container from the VPS:**
```bash
# Requires SSH key-based (passwordless) access to the VPS.
# If you haven't set that up: ssh-copy-id root@187.77.3.56
ssh root@187.77.3.56 'bash -s' < scripts/vps-remove-stray-containers.sh
```

**Step 2 — Reset Kilo on your local Windows machine:**
```powershell
./reset-kilo-extension.ps1
```
Then reload VS Code: `Ctrl+Shift+P` → `Developer: Reload Window`

### Prevention
Always deploy the VPS stack with `--remove-orphans`:
```bash
docker compose up -d --build --remove-orphans
```
This stops any container on the network that is not defined in `docker-compose.yml`.
