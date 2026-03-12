# SNAC-v2: Agent System with Cockpit UI

A modular agent system with RAG, memory timeline, and real-time monitoring cockpit.

## Features

- **Backend API**: FastAPI with agent runtime, RAG ingestion, and task execution
- **Cockpit UI**: Real-time monitoring with three panels:
  - Memory Timeline: View agent actions and ingested documents
  - Node Visualizer: See agent workflow execution
  - Token Cost Monitor: Track API usage and budget
- **Infrastructure**: PostgreSQL, Redis, Qdrant vector database
- **Orchestration**: Docker Compose for easy deployment

## Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenAI API key (for LLM capabilities)

### Setup

1. Clone the repository
2. Create `.env` file:
   ```bash
   cp .env.example .env
   # Edit .env to add your OPENAI_API_KEY
   ```

3. Start the system:
   ```bash
   docker compose up -d --build
   ```

4. Access the cockpit at: http://localhost

### Test the System

Run the test script to verify everything works:
```bash
python test_setup.py
```

Or manually test with curl:
```bash
# Ingest a document
curl -X POST http://localhost/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"content": "The capital of Japan is Tokyo. 2+2=4."}'

# Run an agent task
curl -X POST http://localhost/api/agent/run \
  -H "Content-Type: application/json" \
  -d '{"task": "QUERY: What is the capital of Japan? Then CALC: 25 * 4"}'
```

## Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌────────────────┐
│   Nginx Proxy   │───▶│              │    │                │
│  (ports 80/443) │    │  Backend API │    │   Frontend     │
└─────────────────┘    │  (port 8000) │    │  (port 3000)   │
                       │              │    │                │
                       └──────────────┘    └────────────────┘
                                │
        ┌─────────────┬─────────┴─────────┬─────────────┐
        ▼             ▼                   ▼             ▼
   PostgreSQL    Redis           Qdrant        (Volumes)
   (db)         (redis)        (qdrant)     (postgres_data,
                                            qdrant_data)
```

## API Endpoints

- `GET /` - Health check
- `POST /ingest` - Ingest document for RAG
- `POST /agent/run` - Execute agent task
- `GET /memory/timeline` - Get memory timeline events
- `GET /tokens/usage` - Get token usage statistics

## Development

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend
```bash
cd ui
npm install
npm run dev
```

## Configuration

Edit `.env` to configure:
- `OPENAI_API_KEY` - OpenAI API key (required for LLM features)
- `POSTGRES_PASSWORD` - Database password
- Other service URLs/ports as needed

## License

MIT
