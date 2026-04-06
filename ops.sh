#!/bin/bash

set -e

OPENROUTER_URL="https://we.taile9966e.ts.net/openrouter"
UI_PORT=5173

help() {
    echo "Usage: ./ops.sh <command>"
    echo ""
    echo "Commands:"
    echo "  validate-openrouter   Validate OpenRouter API endpoint"
    echo "  expose-ui             Expose UI via Tailscale"
    echo "  run-tests             Run Playwright UI tests"
    echo "  fix-qdrant            Check and restart Qdrant if unhealthy"
    echo "  add-service           Expose additional port via Tailscale"
    echo "  help                  Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./ops.sh validate-openrouter"
    echo "  ./ops.sh expose-ui"
    echo "  ./ops.sh add-service 8080"
}

validate_openrouter() {
    echo "Validating OpenRouter at $OPENROUTER_URL..."
    
    RESPONSE=$(curl -s -X POST "$OPENROUTER_URL" \
        -H "Content-Type: application/json" \
        -d '{"prompt": "Write a two-sentence summary of quantum computing."}')
    
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to connect to OpenRouter"
        exit 1
    fi
    
    if echo "$RESPONSE" | grep -q "response" && echo "$RESPONSE" | grep -q "model"; then
        echo "SUCCESS: OpenRouter is working"
        echo "Response: $RESPONSE"
    else
        echo "WARNING: Unexpected response format"
        echo "Response: $RESPONSE"
    fi
}

expose_ui() {
    echo "Exposing UI on port $UI_PORT via Tailscale..."
    
    if ! command -v tailscale &> /dev/null; then
        echo "ERROR: tailscale command not found"
        exit 1
    fi
    
    tailscale serve --bg "http://localhost:$UI_PORT"
    
    if [ $? -eq 0 ]; then
        echo "SUCCESS: UI exposed"
        echo "URL: https://$(tailscale ip -4).ts.net"
    else
        echo "ERROR: Failed to expose UI via Tailscale"
        exit 1
    fi
}

run_tests() {
    echo "Running Playwright UI tests..."
    
    if [ ! -d "ui" ]; then
        echo "ERROR: ui directory not found"
        exit 1
    fi
    
    cd ui
    
    if [ ! -d "node_modules" ]; then
        echo "Installing dependencies..."
        npm install
    fi
    
    if grep -q '"test:ui:auto"' package.json; then
        npm run test:ui:auto
    else
        echo "WARNING: test:ui:auto script not found, using test:ui"
        npm run test:ui
    fi
    
    cd ..
}

fix_qdrant() {
    echo "Checking Qdrant health..."
    
    if ! command -v docker &> /dev/null; then
        echo "ERROR: docker command not found"
        exit 1
    fi
    
    LOGS=$(docker compose logs qdrant 2>&1 | tail -20)
    
    if echo "$LOGS" | grep -qi "error\|fatal\|panic"; then
        echo "Qdrant appears unhealthy, restarting..."
        docker compose restart qdrant
        echo "Qdrant restarted"
    else
        echo "Qdrant is healthy"
    fi
}

add_service() {
    local PORT=$1
    
    if [ -z "$PORT" ]; then
        echo "ERROR: Port number required"
        echo "Usage: ./ops.sh add-service <port>"
        exit 1
    fi
    
    echo "Exposing port $PORT via Tailscale..."
    
    if ! command -v tailscale &> /dev/null; then
        echo "ERROR: tailscale command not found"
        exit 1
    fi
    
    tailscale serve --bg "http://localhost:$PORT"
    
    if [ $? -eq 0 ]; then
        echo "SUCCESS: Port $PORT exposed"
        echo "URL: https://$(tailscale ip -4).ts.net:$PORT"
    else
        echo "ERROR: Failed to expose port via Tailscale"
        exit 1
    fi
}

case "$1" in
    validate-openrouter)
        validate_openrouter
        ;;
    expose-ui)
        expose_ui
        ;;
    run-tests)
        run_tests
        ;;
    fix-qdrant)
        fix_qdrant
        ;;
    add-service)
        add_service "$2"
        ;;
    help|--help|-h)
        help
        ;;
    *)
        echo "Unknown command: $1"
        help
        exit 1
        ;;
esac