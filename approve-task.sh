#!/bin/bash
# Keyboard-driven task approval for SNAC v2
# Usage: ./approve-task.sh "TASK DESCRIPTION"

VPS_IP="187.77.3.56"
API_URL="http://\${VPS_IP}:8000"
MAX_TIMEOUT=30  # 30 seconds for curl
MAX_RETRIES=3

if [ -z "\$1" ]; then
    echo "Usage: \$0 \"TASK DESCRIPTION\""
    echo "Example: \$0 \"QUERY: What is 2+2? Then CALC: result * 3\""
    exit 1
fi

TASK="\$1"

# Sanitize task input to prevent command injection
# Remove quotes, backslashes, and shell metacharacters
SANITIZED_TASK=\$(echo "\$TASK" | sed 's/[;&|<>\$()]/_/g' | sed 's/^\s*//g' | sed 's/\s*\$//g')

echo "Sending task to SNAC v2 agent..."
echo "Task: \$SANITIZED_TASK"

# Function to retry curl on failure
do_curl() {
    local attempt=\$1
    local retry_count=0

    while [[ \$retry_count -lt \$MAX_RETRIES ]]; do
        # Send task to agent with timeout
        response=\$(curl -s --max-time \$MAX_TIMEOUT -X POST "\${API_URL}/agent/run" \
            -H "Content-Type: application/json" \
            --connect-timeout \$((MAX_TIMEOUT + 5)) \
            -d "{\"task\":\"\${SANITIZED_TASK}\"}")

        # Check curl exit code
        curl_exit=\$?

        # Parse and display result
        if echo "\$response" | jq -q '.status'; then
            status=\$(echo "\$response" | jq -r '.status // empty')
            if [[ "\$status" == "completed" ]]; then
                result=\$(echo "\$response" | jq -r '.final_result // empty')
                echo "TASK COMPLETE"
                echo "Result: \$result"
                return 0
            elif [[ "\$status" == "error" ]]; then
                error=\$(echo "\$response" | jq -r '.error // empty')
                echo "TASK ERROR"
                echo "Error: \$error"
                [[ \$attempt -eq 1 ]] && echo "(Attempt \$attempt/\$MAX_RETRIES - retrying...)"
            else
                echo "Unknown response status: \$status"
                echo "Response: \$response"
            fi
        else
            echo "Failed to parse response (jq may not be available)"
            echo "Response: \$response"
        fi

        # Retry on failure
        if [[ \$curl_exit -ne 0 ]] && [[ \$retry_count -lt \$((MAX_RETRIES - 1)) ]]; then
            echo "Curl failed (exit code: \$curl_exit). Retrying in 5 seconds..."
            sleep 5
            retry_count=\$((retry_count + 1))
        else
            return \$curl_exit
        fi
    done

    # Give up after max retries
    echo "Max retries reached. Giving up."
    return 1
}

# Check if jq is available
if command -v jq &> /dev/null; then
    do_curl
else
    echo "WARNING: jq not available. Using grep for parsing."
    # Fallback parsing without jq
    response=\$(curl -s --max-time \$MAX_TIMEOUT -X POST "\${API_URL}/agent/run" \
        -H "Content-Type: application/json" \
        --connect-timeout \$((MAX_TIMEOUT + 5)) \
        -d "{\"task\":\"\${SANITIZED_TASK}\"}")

    if echo "\$response" | grep -q '"status":"completed"'; then
        result=\$(echo "\$response" | grep -o '"final_result":"[^"]*"' | cut -d'"' -f4)
        echo "TASK COMPLETE"
        echo "Result: \$result"
    elif echo "\$response" | grep -q '"status":"error"'; then
        error=\$(echo "\$response" | grep -o '"error":"[^"]*"' | cut -d'"' -f4)
        echo "TASK ERROR"
        echo "Error: \$error"
    else
        echo "Unknown response"
        echo "Response: \$response"
    fi
fi
