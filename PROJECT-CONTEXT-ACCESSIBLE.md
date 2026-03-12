# SNAC v2 ACCESSIBILITY CONTEXT FILE (Kilo/TTS Optimized)
# → READ THIS FIRST WHEN RETURNING TO PROJECT
# → STRUCTURED FOR PREDICTABLE TEXT-TO-SPEECH CONSUMPTION

## 🔑 SECTION 1: CONNECTION INFO (READ FIRST)
- VPS IP: 187.77.3.56
- SSH User: root
- Project Path: /opt/agent-system
- Cockpit URL: http://187.77.3.56:3000
- n8n URL: http://187.77.3.56:5678
- Backend API: http://187.77.3.56:8000

## 🛠️ SECTION 2: QUICK-START COMMANDS (COPY-PASTE READY)

# 1. CONNECT TO VPS
ssh root@187.77.3.56

# 2. NAVIGATE TO PROJECT
cd /opt/snac-v2/backend

# 3. VERIFY INFRASTRUCTURE HEALTH (MUST HEAR "healthy" FOR ALL SERVICES)
docker compose ps

# 4. IF UNHEALTHY, RESTART INFRASTRUCTURE ONLY (PRESERVES VOLUMES/.env):
docker compose up -d postgres redis qdrant nginx

# 5. START AGENT STACK (backend, cockpit, n8n):
docker compose up -d backend cockpit n8n

# 6. VERIFY COCKPIT IS ACCESSIBLE:
curl -s http://localhost:8000/health

# 7. SEND A TEST TASK TO CONFIRM FLOW:
curl -s -X POST http://localhost:8000/agent/run \
  -H "Content-Type: application/json" \
  -d '{"task":"QUERY: What is 2+2? Then CALC: result * 3"}'

## 👂 SECTION 3: TTS-FRIENDLY ALERT SYSTEM (HEAR THESE AUDIO CUES)
# → THESE ARE AUTOMATICALLY SPOKEN BY YOUR SYSTEM (NO ACTION NEEDED)
# [ALERT: TASK START] → Spoken when agent begins processing a task
# [ALERT: TASK COMPLETE] → Spoken when agent finishes (with final result)
# [ALERT: COST SPIKE] → Spoken if daily estimate exceeds budget threshold
# [ALERT: TOOL ERROR] → Spoken if a tool fails (e.g., invalid CALC input)
# [ALERT: WS CONNECTED] → Spoken when WebSocket links cockpit/backend

## 📝 SECTION 4: NOTES FOR YOUR TTS ENGINE
# → CONFIGURE THESE IN YOUR TTS SOFTWARE FOR BEST EXPERIENCE
# Voice: Female, medium pace
# Rate: 180-200 wpm (adjust to your comprehension speed)
# Pauses: 0.5s between sections, 1.0s between alerts
# Pronunciation:
#   - "QUERY:" → "query"
#   - "CALC:" → "calculate"
#   - "RESULT:" → "result"
#   - "WS:" → "web socket"
#   - "JSON:" → "jay sahn"

## 🔧 SECTION 5: LOCAL SCRIPTS (RUN ON YOUR MACHINE)

# TTS Proxy - Listens to WebSocket and speaks events
# Location: ~/agent-system/tts-proxy.sh
# Usage: ~/agent-system/tts-proxy.sh

# Task Approval - Keyboard-driven task submission
# Location: ~/agent-system/approve-task.sh
# Usage: ~/agent-system/approve-task.sh "QUERY: What is 2+2?"
