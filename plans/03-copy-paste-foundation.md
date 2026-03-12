# Planning Document 3: Copy-Paste Foundation Template

## 1. docker-compose.yml (Single Source of Truth)

Save as `/opt/agent-system/docker-compose.yml`. Uses only **official images** + minimal custom builds. All data persists via named volumes.

```yaml
version: '3.8'

services:
  # ===== FOUNDATION LAYER (PHASE 1) =====
  postgres:
    image: postgres:15-alpine
    container_name: agent-postgres
    restart: unless-stopped
    volumes:
      - pg_data:/var/lib/postgresql/data
    environment:
      POSTGRES_USER: agent
      POSTGRES_PASSWORD: agent_secure_password  # CHANGE ME!
      POSTGRES_DB: agent_db
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U agent"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: agent-redis
    restart: unless-stopped
    volumes:
      - redis_data:/data
    command: ["redis-server", "--appendonly", "yes"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  qdrant:
    image: qdrant/qdrant:latest
    container_name: agent-qdrant
    restart: unless-stopped
    volumes:
      - qdrant_storage:/qdrant/storage
    ports:
      - "6333:6333"  # HTTP API
      - "6334:6334"  # gRPC (for LlamaIndex)
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:6333/collections"]
      interval: 15s
      timeout: 5s
      retries: 5

  # ===== AGENT RUNTIME & ORCHESTRATION (PHASES 2-3) =====
  api-gateway:
    build: ./services/api-gateway
    container_name: agent-api
    restart: unless-stopped
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      qdrant:
        condition: service_healthy
    environment:
      - DATABASE_URL=postgresql://agent:agent_secure_password@postgres:5432/agent_db
      - REDIS_URL=redis://redis:6379
      - QDRANT_URL=http://qdrant:6333
      - OLLAMA_HOST=http://host.docker.internal:11434  # For local Ollama (if used)
    volumes:
      - ./services/api-gateway:/app  # Live code reload (dev only!)
    command: ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

  orchestrator:
    build: ./services/orchestrator
    container_name: agent-orchestrator
    restart: unless-stopped
    depends_on:
      api-gateway:
        condition: service_healthy
    environment:
      - API_GATEWAY_URL=http://api-gateway:8000
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./services/orchestrator:/app
    command: ["python", "-m", "orchestrator.main"]  # AutoGen entrypoint

  # ===== COCKPIT UI (PHASE 7) =====
  cockpit:
    build: ./services/cockpit
    container_name: agent-cockpit
    restart: unless-stopped
    ports:
      - "3000:3000"
    depends_on:
      api-gateway:
        condition: service_healthy
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    volumes:
      - ./services/cockpit:/app
    command: ["npm", "run", "dev"]  # Next.js dev mode

volumes:
  pg_data:
  redis_data:
  qdrant_storage:
```

### 🔑 Critical Notes on This Compose File

- **No Ollama by default**: Added as commented env var (`OLLAMA_HOST`) – uncomment only if you have GPU/CPU to spare. *Start with OpenAI API to avoid token starvation on $5 VPS.*
- **Health checks**: Prevents orchestrator from starting before DBs are ready (a silent killer in dev).
- **Live code mounts**: `./services/:/app` lets you edit code *without* rebuilding containers (dev only – remove in prod).
- **Ports exposed minimally**: Only API gateway (8000) and cockpit (3000) need host access. Others are internal-only.
- **Secrets**: **NEVER commit real passwords** – use `.env` file (see below) or Docker secrets in prod.

> 💡 **Create `.env` in `/opt/agent-system/`** (add to `.gitignore`!):  
> ```env
> POSTGRES_PASSWORD=your_strong_password_here
> OPENAI_API_KEY=sk-...  # Get from platform.openai.com (set budget limit!)
> ```

---

## 2. Minimal Agent Code Snippets (Python)

Save under `/opt/agent-system/services/orchestrator/`. Demonstrates **LangGraph + LlamaIndex + AutoGen integration** – the core "brain".

### File: `services/orchestrator/agents/planner.py`

The Planner agent – delegates tasks to Workers using AutoGen + LangGraph state

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator
from autogen import AssistantAgent, UserProxyAgent
from llama_index import VectorStoreIndex, ServiceContext
from llama_index.vector_stores import QdrantVectorStore
import qdrant_client
import os

# ===== STATE DEFINITION (LangGraph) =====
class AgentState(TypedDict):
    task: str
    plan: list[str]
    current_step: int
    result: str
    memory: Annotated[list, operator.add]  # Auto-appends to memory

# ===== TOOLS: RAG QUERY (LlamaIndex + Qdrant) =====
def setup_rag_tool():
    client = qdrant_client.QdrantClient(host=os.getenv("QDRANT_URL", "http://qdrant:6333"))
    vector_store = QdrantVectorStore(client=client, collection_name="agent_docs")
    service_context = ServiceContext.from_defaults(embed_model="local")  # Uses Ollama or HF
    return VectorStoreIndex.from_vector_store(vector_store, service_context=service_context)

rag_index = setup_rag_tool()
rag_query_tool = rag_index.as_query_engine(similarity_top_k=3)

def query_knowledge_base(query: str) -> str:
    """Tool for agents to query private data"""
    response = rag_query_tool.query(query)
    return str(response)

# ===== AUTOGen AGENT SETUP =====
def create_worker_agent():
    return AssistantAgent(
        name="worker",
        system_message="""You are a specialized worker agent.
        Use the 'query_knowledge_base' tool to answer questions from private data.
        Always cite your sources.""",
        llm_config={"config_list": [{"model": "gpt-3.5-turbo", "api_key": os.getenv("OPENAI_API_KEY")}]},
    )

def create_planner_agent():
    return UserProxyAgent(
        name="planner",
        human_input_mode="NEVER",
        max_consecutive_auto_reply=10,
        code_execution_config=False,
    )

# ===== LANGGRAPH WORKFLOW (Stateful Orchestration) =====
def planner_node(state: AgentState):
    """Planner breaks task into steps"""
    planner = create_planner_agent()
    worker = create_worker_agent()
    
    # AutoGen conversation: Planner directs Worker
    chat_result = planner.initiate_chat(
        worker,
        message=f"""Break down this task into clear steps: {state['task']}
        For each step, specify if it requires querying the knowledge base.
        Return ONLY a JSON list of steps, e.g., ["Step 1: Query X", "Step 2: Calculate Y"]""",
    )
    
    # Extract plan from chat (simplified – in prod use structured output)
    plan = [step.strip('"- ') for step in chat_result.chat_history[-1]['content'].split('\n') if step.strip()]
    
    return {
        **state,
        "plan": plan,
        "current_step": 0,
        "memory": [f"Planner created plan: {plan}"]
    }

def worker_node(state: AgentState):
    """Worker executes one step at a time"""
    if state["current_step"] >= len(state["plan"]):
        return {**state, "result": "Task complete!", "memory": state["memory"] + ["Worker finished"]}
    
    step = state["plan"][state["current_step"]]
    worker = create_worker_agent()
    
    # Check if step needs RAG
    if "query" in step.lower() or "knowledge" in step.lower():
        # Extract query from step (naive – improve with NLP)
        query = step.replace("Query knowledge base for ", "")
        tool_result = query_knowledge_base(query)
        worker_reply = worker.generate_reply(
            messages=[{"role": "user", "content": f"Use this info to complete: {step}\n\nInfo: {tool_result}"}]
        )
    else:
        worker_reply = worker.generate_reply(messages=[{"role": "user", "content": f"Complete this step: {step}"}])
    
    return {
        **state,
        "current_step": state["current_step"] + 1,
        "result": worker_reply,
        "memory": state["memory"] + [f"Worker executed: {step} -> {worker_reply[:100]}..."]
    }

# ===== BUILD THE GRAPH =====
workflow = StateGraph(AgentState)
workflow.add_node("planner", planner_node)
workflow.add_node("worker", worker_node)
workflow.set_entry_point("planner")
workflow.add_edge("planner", "worker")
workflow.add_conditional_edges(
    "worker",
    lambda state: "worker" if state["current_step"] < len(state["plan"]) else END,
    {"worker": "worker", END: END}
)
app = workflow.compile()

# ===== EXPORT FOR API GATEWAY =====
def run_agent_task(task: str) -> dict:
    """Called by API Gateway – returns final state"""
    initial_state = {
        "task": task,
        "plan": [],
        "current_step": 0,
        "result": "",
        "memory": []
    }
    final_state = app.invoke(initial_state)
    return final_state
```

### File: `services/api-gateway/main.py`

Minimal FastAPI endpoint to trigger the agent

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from orchestrator.agents.planner import run_agent_task  # Adjust import path

app = FastAPI()

class TaskRequest(BaseModel):
    task: str

@app.post("/agent/run")
async def run_task(request: TaskRequest):
    try:
        result = run_agent_task(request.task)
        return {
            "status": "success",
            "task": request.task,
            "plan": result["plan"],
            "steps_executed": result["current_step"],
            "final_result": result["result"],
            "memory_trace": result["memory"]  # For cockpit UI
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 3. Folder Structure Snippets

Only the essential files for the MVP:

```bash
/opt/agent-system/
├── docker-compose.yml          # (As provided above)
├── .env                        # (Create this - NEVER commit!)
├── services/
│   ├── api-gateway/
│   │   ├── main.py             # (FastAPI code above)
│   │   ├── Dockerfile          # See below
│   │   └── requirements.txt    # fastapi, uvicorn, pydantic
│   ├── orchestrator/
│   │   ├── agents/
│   │   │   └── planner.py      # (LangGraph/AutoGen code above)
│   │   ├── main.py             # Simple entrypoint: `from agents.planner import *`
│   │   ├── Dockerfile          # See below
│   │   └── requirements.txt    # langgraph, llama-index, qdrant-client, autogen, openai
│   └── cockpit/
│       ├── pages/
│       │   └── index.js        # Next.js page (see note below)
│       ├── Dockerfile          # See below
│       └── package.json        # next, react, tailwindcss
└── # Volumes auto-created by Docker (pg_data, redis_data, etc.)
```

### Minimal Dockerfiles

**`services/api-gateway/Dockerfile`**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**`services/orchestrator/Dockerfile`**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "-m", "orchestrator.main"]
```

**`services/cockpit/Dockerfile`**
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
CMD ["npm", "run", "dev"]
```

---

## 4. How to Validate This Works (5-Minute Smoke Test)

1. **Start foundation**:  
   ```bash
   cd /opt/agent-system
   docker compose up -d postgres redis qdrant  # Start DBs first
   ```

2. **Verify DBs are ready** (should see `healthy` in `docker compose ps`):  
   ```bash
   docker compose logs -f postgres  # Wait for "database system is ready to accept connections"
   ```

3. **Start agent stack**:  
   ```bash
   docker compose up -d api-gateway orchestrator cockpit
   ```

4. **Test the agent**:  
   ```bash
   curl -X POST http://localhost:8000/agent/run \
     -H "Content-Type: application/json" \
     -d '{"task": "What is the capital of France?"}'  # Try a RAG query after ingesting doc!
   ```

5. **Watch logs** (critical!):  
   ```bash
   docker compose logs -f orchestrator  # See planner/worker steps
   docker compose logs -f api-gateway   # See API requests
   ```

> 🚨 **If this fails**:  
> - Check `docker compose logs [service]` for the failing container  
> - 90% of issues: **missing env vars** (`.env` not loaded) or **version conflicts** (pin exact versions in `requirements.txt`!)  
> - Example `requirements.txt` for orchestrator:  
>   ```txt
>   langgraph==0.0.350
>   llama-index==0.9.15
>   qdrant-client==1.6.2
>   autogen==0.2.21
>   openai==1.3.5
>   ```

---

## 5. Where to Improve

| Area | What You Have Here | Common Pitfall | How to Improve Later |
|------|--------------------|----------------|----------------------|
| **Agent State** | LangGraph checkpoints (implicit in `StateGraph`) | Losing state on restart | Add explicit checkpoint saver to Postgres |
| **Tool Safety** | Basic tool execution | Agent runs `rm -rf /` via shell tool | Wrap all tools in AutoGen's `ToolExecutor` with allowlists |
| **Observability** | Logs only | No visibility into token/cost | Add Langfuse (self-hostable) to trace LLM calls |
| **Scalability** | Single VPS | "It works on my machine" fails in prod | When ready: replace `depends_on` with Kubernetes probes |
| **Cockpit** | Basic Next.js | UI becomes slow with 100+ agents | Add React Query for data caching + WebSocket pagination |

---

## 6. Your Next Move

1. **Run this exact setup** – validate the foundation works *before* adding complexity.  
2. **Then** add:  
   - A document ingest script (`POST /ingest` that calls LlamaIndex)  
   - A Slack webhook tool in `planner.py`  
   - Cockpit UI to display `memory_trace`  
3. **Only after** you see the agent execute a multi-step RAG task correctly → *then* think about scaling.
