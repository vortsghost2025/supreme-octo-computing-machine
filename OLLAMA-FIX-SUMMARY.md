# Ollama Connection Fix Summary

## Problem Identified
Your system has **TWO separate Ollama instances** running:
1. Port 11434 (default) - EMPTY models list
2. Port 9001 - Has all your models (mistral:7b, llama3, etc.)

Backend was trying to connect to port 11434, getting empty results.

## Changes Made

### 1. Docker Compose Configuration Updated
- Changed `OLLAMA_BASE_URL` from `http://187.77.3.56:11434` (VPS) to `http://host.docker.internal:9001` (local)
- Changed default model from `llama3.2:3b` to `mistral:7b`
- Backend now runs on port **8001** instead of 8000 (Manager.exe was blocking 8000)

### 2. Connection Verified
```bash
# From inside container, connection works:
docker exec snac_backend python -c "import httpx; print(httpx.get('http://host.docker.internal:9001/api/tags').status_code)"
# Output: 200
```

### 3. Available Models
- mistral:7b
- mistral-working:latest
- mistral-small3.2:latest
- llama3:8b-instruct-q4_K_M
- orca-mini:latest

## Current Status

### ✅ Working
- Ollama running on port 9001 with models
- Backend container running on port 8001
- Connection from container to Ollama: SUCCESS
- Health endpoint: http://localhost:8001/health

### ⚠️ Issue Remaining
The `/llm/models` endpoint returns 503 error despite connection working. This appears to be a timeout issue in the async client configuration.

## Immediate Workaround

**Use direct generation instead:**
```bash
# Test generation directly
curl -X POST http://localhost:8001/llm \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Hello, how are you?","model":"mistral:7b"}'
```

## Alternative: Run Backend Locally

For faster iteration, run backend outside Docker:
```bash
cd backend
OLLAMA_BASE_URL=http://localhost:9001 \
OLLAMA_MODEL=mistral:7b \
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

This connects directly to local Ollama without Docker networking.

## Next Steps

1. Test the `/llm` endpoint directly (not `/llm/models`)
2. If still failing, run backend locally for debugging
3. Check async client timeout settings in llm_client.py

## Files Modified
- docker-compose.yml (OLLAMA_BASE_URL, OLLAMA_MODEL, port mapping)
- .env (added OLLAMA_BASE_URL)
- Created start-ollama-networked.ps1
- Created start-ollama-networked.bat

## Verification Commands
```bash
# Check Ollama has models
curl http://localhost:9001/api/tags

# Check backend health
curl http://localhost:8001/health

# Test connection from container
docker exec snac_backend python -c "import httpx; print(httpx.get('http://host.docker.internal:9001/api/tags').json()['models'][0]['name'])"

# Check backend logs
docker logs snac_backend --tail 20
```
