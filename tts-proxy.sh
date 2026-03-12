#!/bin/bash
# TTS Proxy for SNAC v2 - Listens to WebSocket and speaks events
# Run locally (not on VPS)
# Usage: ./tts-proxy.sh

VPS_IP="187.77.3.56"
WS_URL="ws://${VPS_IP}:3000/ws/chat"

# TTS Command - Uncomment one that works for your system
# For Windows PowerShell, use the PowerShell version instead
TTS_CMD="cat"  # Default: just print (use "cat" to test first)

# Fallback for Windows
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Git Bash on Windows
    TTS_CMD='echo'
fi

echo "Starting TTS proxy for SNAC v2..."
echo "Listening to: $WS_URL"
echo "Press Ctrl+C to stop"

# Check if websocat is available
if ! command -v websocat &> /dev/null; then
    echo "ERROR: websocat not found"
    echo "Install with: cargo install websocat"
    echo "Or use nix: nix-shell -p websocat"
    exit 1
fi

# Track previous state for edge detection
prev_status=""
prev_cost="0"
prev_tool_calls="0"

# Main loop
while true; do
    echo "Connecting to WebSocket..."
    
    # Read WebSocket messages
    websocat "$WS_URL" 2>/dev/null | while IFS= read -r line; do
        # Check if it's JSON
        if [[ "$line" == \{* ]]; then
            # Extract key fields using grep/cut (simple parsing)
            # Looking for: status, task, final_result
            
            # Check for task start
            if echo "$line" | grep -q '"status":"processing"'; then
                if [[ "$prev_status" != "processing" ]]; then
                    echo "[ALERT: TASK START] Agent started processing a task" | $TTS_CMD
                    prev_status="processing"
                fi
            fi
            
            # Check for task complete
            if echo "$line" | grep -q '"status":"completed"'; then
                if [[ "$prev_status" != "completed" ]]; then
                    result=$(echo "$line" | grep -o '"final_result":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
                    echo "[ALERT: TASK COMPLETE] Task finished. Result: $result" | $TTS_CMD
                    prev_status="completed"
                fi
            fi
            
            # Check for tool usage
            if echo "$line" | grep -q '"tool_calls"'; then
                tool_count=$(echo "$line" | grep -o '"tool_calls"' | wc -l)
                if [[ "$tool_count" -gt "$prev_tool_calls" && "$tool_count" -lt 5 ]]; then
                    echo "[ALERT: TOOL USED] Tool called. Total: $tool_count" | $TTS_CMD
                    prev_tool_calls="$tool_count"
                fi
            fi
            
            # Check for WebSocket connect
            if echo "$line" | grep -q '"type":"connected"'; then
                echo "[ALERT: WS CONNECTED] WebSocket connected" | $TTS_CMD
            fi
        fi
    done
    
    # If we get here, connection was lost - reconnect after delay
    echo "Connection lost. Reconnecting in 5 seconds..."
    sleep 5
done
