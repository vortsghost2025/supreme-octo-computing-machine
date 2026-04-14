#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

validate_openrouter() {
    log_info "Validating OpenRouter endpoint..."
    
    local response
    response=$(curl -s -X POST "https://we.taile9966e.ts.net/openrouter" \
        -H "Content-Type: application/json" \
        -d '{"prompt": "Write a two-sentence summary of quantum computing."}' \
        2>&1) || {
            log_error "Failed to connect to OpenRouter endpoint"
            echo "$response"
            return 1
        }
    
    echo "$response" | grep -q '"success"' && {
        log_info "OpenRouter validation successful!"
        echo "$response"
        return 0
    } || {
        log_error "OpenRouter validation failed"
        echo "$response"
        return 1
    }
}

expose_ui() {
    log_info "Exposing UI via Tailscale..."
    
    tailscale serve --bg http://localhost:5173
    
    local url
    url=$(tailscale serve --json 2>/dev/null | grep -o '"https://[^"]*\.ts\.net"' | head -1 || echo "")
    
    if [[ -n "$url" ]]; then
        log_info "UI exposed at: $url"
    else
        log_warn "UI exposed. Run 'tailscale serve' to see the URL."
    fi
}

run_tests() {
    log_info "Running Playwright tests..."
    
    cd ui/
    
    if [[ ! -d "node_modules" ]]; then
        log_info "Installing dependencies..."
        npm install
    fi
    
    npm run test:ui:auto
}

fix_qdrant() {
    log_info "Checking Qdrant health..."
    
    local status
    status=$(docker compose ps qdrant --format json 2>/dev/null | grep -o '"Status":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
    
    if [[ "$status" != *"Up"* ]]; then
        log_warn "Qdrant is unhealthy (status: $status). Restarting..."
        docker compose restart qdrant
        sleep 5
        log_info "Qdrant restarted."
    else
        log_info "Qdrant is healthy (status: $status)"
    fi
}

add_service() {
    local port="${1:-3000}"
    local name="${2:-service}"
    
    if [[ -z "$port" ]]; then
        log_error "Port is required. Usage: ops.sh add-service <port> [name]"
        return 1
    fi
    
    log_info "Exposing port $port via Tailscale as '$name'..."
    
    tailscale serve --bg "http://localhost:$port" "$name"
    
    log_info "Port $port exposed as '$name'"
}

show_help() {
    cat <<EOF
Local Operations Script

Usage: $0 <command> [arguments]

Commands:
    validate-openrouter    Validate OpenRouter endpoint
    expose-ui              Expose UI via Tailscale
    run-tests              Run Playwright tests
    fix-qdrant             Check and restart Qdrant if unhealthy
    add-service <port> [name]   Expose additional port via Tailscale
    help                   Show this help message

Examples:
    $0 validate-openrouter
    $0 expose-ui
    $0 run-tests
    $0 fix-qdrant
    $0 add-service 3000 myapp
    $0 add-service 8080 api
EOF
}

case "${1:-help}" in
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
        add_service "$2" "$3"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac