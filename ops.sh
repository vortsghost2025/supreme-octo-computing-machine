#!/bin/bash

set -e

OPENROUTER_URL="${OPENROUTER_URL:-https://we.taile9966e.ts.net/openrouter}"
UI_PORT="${UI_PORT:-5173}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

usage() {
    cat <<EOF
Usage: $0 <command>

Commands:
    validate-openrouter    Validate OpenRouter API connectivity
    expose-ui            Expose UI via Tailscale (port $UI_PORT)
    expose-port <port>   Expose additional port via Tailscale
    run-tests            Run Playwright UI tests
    fix-qdrant           Check and restart Qdrant if unhealthy
    help                Show this help message

Examples:
    $0 validate-openrouter
    $0 expose-ui
    $0 expose-port 8000
    $0 run-tests
    $0 fix-qdrant

Environment Variables:
    OPENROUTER_URL    OpenRouter API URL (default: https://we.taile9966e.ts.net/openrouter)
    UI_PORT          UI port to expose (default: 5173)
    COMPOSE_FILE     Docker compose file (default: docker-compose.yml)

EOF
}

validate_openrouter() {
    log_info "Validating OpenRouter at $OPENROUTER_URL..."

    local prompt="Write a two-sentence summary of quantum computing."
    local payload=$(jq -n \
        --arg p "$prompt" \
        '{messages: [{role: "user", content: $p}], model: "qwen/qwen-2.5-7b-instruct"}')

    local response
    response=$(curl -s -w "\n%{http_code}" -X POST "$OPENROUTER_URL" \
        -H "Content-Type: application/json" \
        -H "Accept: application/json" \
        -d "$payload" 2>/dev/null) || {
            log_error "Failed to connect to OpenRouter"
            return 1
        }

    local http_code
    http_code=$(echo "$response" | tail -n1)
    local body
    body=$(echo "$response" | sed '$d')

    if [ "$http_code" = "200" ]; then
        if echo "$body" | jq -e '.response, .model, .success' >/dev/null 2>&1; then
            local model
            model=$(echo "$body" | jq -r '.model // "unknown"')
            log_info "OpenRouter validation successful!"
            log_info "Model: $model"
            return 0
        else
            log_warn "OpenRouter responded but format unexpected"
            echo "$body" | jq .
            return 0
        fi
    else
        log_error "OpenRouter returned HTTP $http_code"
        echo "$body" | jq . 2>/dev/null || echo "$body"
        return 1
    fi
}

expose_ui() {
    log_info "Exposing UI on port $UI_PORT via Tailscale..."

    if ! command -v tailscale &>/dev/null; then
        log_error "tailscale command not found"
        return 1
    fi

    tailscale serve --bg "http://localhost:$UI_PORT" 2>/dev/null || {
        log_warn "tailscale serve may already be running, attempting to refresh..."
        tailscale serve --clear 2>/dev/null || true
        tailscale serve --bg "http://localhost:$UI_PORT"
    }

    local url
    url=$(tailscale serve --json 2>/dev/null | jq -r '.http // "unknown"' 2>/dev/null || echo "Check with: tailscale serve -h")

    log_info "UI exposed at: $url"
    log_info "Run 'tailscale serve' to manage exposed services"
}

expose_port() {
    local port="${1:-8000}"

    if [ -z "$port" ]; then
        log_error "Port number required"
        echo "Usage: $0 expose-port <port>"
        return 1
    fi

    log_info "Exposing port $port via Tailscale..."

    if ! command -v tailscale &>/dev/null; then
        log_error "tailscale command not found"
        return 1
    fi

    tailscale serve --bg "http://localhost:$port" 2>/dev/null || {
        log_warn "tailscale serve may already be running on this port"
        tailscale serve --clear 2>/dev/null || true
        tailscale serve --bg "http://localhost:$port"
    }

    log_info "Port $port exposed via Tailscale"
}

run_tests() {
    log_info "Running Playwright UI tests..."

    local ui_dir="ui"

    if [ ! -d "$ui_dir" ]; then
        log_error "UI directory not found: $ui_dir"
        return 1
    fi

    cd "$ui_dir"

    if [ ! -d "node_modules" ]; then
        log_info "Installing npm dependencies..."
        npm install || {
            log_error "npm install failed"
            cd ..
            return 1
        }
    fi

    if ! npm run test:ui:auto &>/dev/null; then
        log_info "Running tests with npm run test:ui:auto..."
        npm run test:ui:auto
    else
        npm run test:ui:auto
    fi

    local exit_code=$?
    cd ..

    if [ $exit_code -eq 0 ]; then
        log_info "All tests passed!"
    else
        log_error "Tests failed with exit code $exit_code"
    fi

    return $exit_code
}

fix_qdrant() {
    log_info "Checking Qdrant status..."

    local service_name="qdrant"
    local logs_cmd="docker compose -f $COMPOSE_FILE logs $service_name"
    local restart_cmd="docker compose -f $COMPOSE_FILE restart $service_name"

    if ! docker compose -f "$COMPOSE_FILE" ps "$service_name" &>/dev/null; then
        log_error "Qdrant service not found in $COMPOSE_FILE"
        return 1
    fi

    local status
    status=$(docker compose -f "$COMPOSE_FILE" ps "$service_name" --format json 2>/dev/null | jq -r '.State' 2>/dev/null || echo "unknown")

    log_info "Qdrant status: $status"

    local health
    health=$(docker inspect --format='{{.State.Health.Status}}' "${service_name}_1" 2>/dev/null || echo "unknown")

    if [ "$health" = "unhealthy" ] || [ "$status" != "running" ]; then
        log_warn "Qdrant is unhealthy, restarting..."
        $restart_cmd

        sleep 2

        local new_status
        new_status=$(docker compose -f "$COMPOSE_FILE" ps "$service_name" --format json 2>/dev/null | jq -r '.State' 2>/dev/null || echo "unknown")

        if [ "$new_status" = "running" ]; then
            log_info "Qdrant restarted successfully"
        else
            log_error "Qdrant restart failed"
            log_error "Recent logs:"
            $logs_cmd --tail 20
            return 1
        fi
    else
        log_info "Qdrant is healthy"
    fi
}

main() {
    local command="${1:-help}"

    case "$command" in
        validate-openrouter)
            validate_openrouter
            ;;
        expose-ui)
            expose_ui
            ;;
        expose-port)
            expose_port "${2:-}"
            ;;
        run-tests|test)
            run_tests
            ;;
        fix-qdrant|qdrant)
            fix_qdrant
            ;;
        help|--help|-h)
            usage
            ;;
        *)
            log_error "Unknown command: $command"
            usage
            exit 1
            ;;
    esac
}

main "$@"