"""
SNAC-v2 Backend API
Agent runtime with RAG, memory timeline, and orchestration.
"""

import os
import re
import time
import json
import asyncio
import ast
import math
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any, Annotated
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
import httpx
from openai import AsyncOpenAI
import redis.asyncio as aioredis
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Agent state storage (in production, use Redis/Postgres)
agent_sessions: Dict[str, Dict[str, Any]] = {}
_fallback_session_last_seen: Dict[str, float] = {}
memory_timeline: List[Dict[str, Any]] = []
token_usage: Dict[str, float] = {"total": 0.0, "by_session": {}}
thought_memory: List[Dict[str, Any]] = []
shared_knowledge_memory: List[Dict[str, Any]] = []
memory_injection_runtime: Dict[str, Dict[str, Any]] = {}
swarm_events: List[Dict[str, Any]] = []
swarm_config: Dict[str, Any] = {
    "min_workers": 2,
    "max_workers": 12,
    "max_tokens_per_min": 80000,
    "max_cpu_percent": 80.0,
    "idle_timeout_seconds": 120,
}
swarm_state: Dict[str, Any] = {
    "active_workers": {},
    "last_scale_down_at": 0.0,
}

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
# Cost per output token in USD; default 0 (unset — avoids misleading charges when key is missing)
_OPENAI_COST_PER_TOKEN = float(os.getenv("OPENAI_COST_PER_TOKEN", "0"))
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "documents")
# In-memory fallback limits
_MEMORY_FALLBACK_SESSION_TTL = int(os.getenv("MEMORY_FALLBACK_SESSION_TTL_SECONDS", "86400"))
_MEMORY_FALLBACK_MAX_SESSIONS = int(os.getenv("MEMORY_FALLBACK_MAX_SESSIONS", "500"))
_MEMORY_FALLBACK_MAX_TIMELINE = int(os.getenv("MEMORY_FALLBACK_MAX_TIMELINE_EVENTS", "10000"))
_MEMORY_FALLBACK_MAX_THOUGHTS = int(os.getenv("MEMORY_FALLBACK_MAX_THOUGHTS", "5000"))
_MEMORY_FALLBACK_MAX_SHARED_KNOWLEDGE = int(os.getenv("MEMORY_FALLBACK_MAX_SHARED_KNOWLEDGE", "5000"))
_MEMORY_FALLBACK_MAX_SWARM_EVENTS = int(os.getenv("MEMORY_FALLBACK_MAX_SWARM_EVENTS", "5000"))
_MEMORY_INJECTION_MAX_ITEMS = int(os.getenv("MEMORY_INJECTION_MAX_ITEMS", "100"))
_MAX_TASK_STEPS = int(os.getenv("MAX_TASK_STEPS", "20"))

_SWARM_QUEUE_KEY_PREFIX = "swarm:queue"
_SWARM_EVENTS_KEY = "swarm:events"
_SWARM_CONFIG_KEY = "swarm:config"
_SWARM_WORKERS_ACTIVE_KEY = "swarm:workers:active"
_MEMORY_SHARED_KNOWLEDGE_KEY = "memory:shared_knowledge"

# OpenAI async client (None when key is absent)
_openai_client: Optional[AsyncOpenAI] = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
# Redis and Qdrant clients are initialized in lifespan
_redis: Optional[aioredis.Redis] = None
_qdrant: Optional[AsyncQdrantClient] = None

_SECRET_PATTERN = re.compile(
    r'(sk-[A-Za-z0-9\-_]{10,}|[Aa][Pp][Ii][-_]?[Kk][Ee][Yy]\s*[:=]\s*\S+)',
    re.IGNORECASE,
)


def _redact_secrets(value: str) -> str:
    """Replace apparent secrets/keys before writing to logs."""
    return _SECRET_PATTERN.sub("[REDACTED]", value)


def _prune_memory_fallback_state() -> None:
    """Evict expired and excess sessions from the in-memory fallback dicts."""
    now = time.time()
    expired = [
        sid for sid, ts in _fallback_session_last_seen.items()
        if now - ts > _MEMORY_FALLBACK_SESSION_TTL
    ]
    for sid in expired:
        agent_sessions.pop(sid, None)
        token_usage["by_session"].pop(sid, None)
        _fallback_session_last_seen.pop(sid, None)

    # Hard cap: evict oldest by last-seen if still over limit
    while len(agent_sessions) > _MEMORY_FALLBACK_MAX_SESSIONS:
        oldest = min(_fallback_session_last_seen, key=_fallback_session_last_seen.get, default=None)
        if oldest is None:
            break
        agent_sessions.pop(oldest, None)
        token_usage["by_session"].pop(oldest, None)
        _fallback_session_last_seen.pop(oldest, None)

    # Cap timeline ring buffer
    if len(memory_timeline) > _MEMORY_FALLBACK_MAX_TIMELINE:
        del memory_timeline[: len(memory_timeline) - _MEMORY_FALLBACK_MAX_TIMELINE]

    # Cap thought cache ring buffer
    if len(thought_memory) > _MEMORY_FALLBACK_MAX_THOUGHTS:
        del thought_memory[: len(thought_memory) - _MEMORY_FALLBACK_MAX_THOUGHTS]

    # Cap shared knowledge ring buffer
    if len(shared_knowledge_memory) > _MEMORY_FALLBACK_MAX_SHARED_KNOWLEDGE:
        del shared_knowledge_memory[: len(shared_knowledge_memory) - _MEMORY_FALLBACK_MAX_SHARED_KNOWLEDGE]

    # Cap swarm event buffer
    if len(swarm_events) > _MEMORY_FALLBACK_MAX_SWARM_EVENTS:
        del swarm_events[: len(swarm_events) - _MEMORY_FALLBACK_MAX_SWARM_EVENTS]


def _get_allowed_origins() -> List[str]:
    """Resolve allowed CORS origins from env for safer production defaults."""
    raw = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global _redis, _qdrant
    print("SNAC-v2 Backend starting up...")
    print(f"OpenAI API: {'configured' if OPENAI_API_KEY else 'MISSING'}")

    try:
        _redis = aioredis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
        await _redis.ping()
        print(f"Redis: connected at {REDIS_HOST}:{REDIS_PORT}")
    except Exception as e:
        print(f"Redis: unavailable ({_redact_secrets(str(e))}) - using in-memory fallback")
        _redis = None

    try:
        _qdrant = AsyncQdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, check_compatibility=False)
        collections = await _qdrant.get_collections()
        names = [c.name for c in collections.collections]
        if QDRANT_COLLECTION not in names:
            await _qdrant.create_collection(
                collection_name=QDRANT_COLLECTION,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
            )
            print(f"Qdrant: created collection '{QDRANT_COLLECTION}'")
        else:
            print(f"Qdrant: collection '{QDRANT_COLLECTION}' ready")
    except Exception as e:
        print(f"Qdrant: unavailable ({_redact_secrets(str(e))}) - RAG disabled")
        _qdrant = None

    yield

    if _redis:
        await _redis.aclose()
    if _qdrant:
        await _qdrant.close()
    print("SNAC-v2 Backend shutting down...")


app = FastAPI(
    title="SNAC-v2 Agent API",
    description="Agent runtime with RAG and memory timeline",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============== MODELS ==============

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    service: str
    services: Dict[str, str]


class IngestRequest(BaseModel):
    content: Annotated[str, Field(min_length=1, max_length=50000)]
    metadata: Optional[Dict[str, Any]] = None

    @field_validator("content")
    @classmethod
    def content_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("content must not be blank")
        return v


class IngestResponse(BaseModel):
    success: bool
    chunks: int
    document_id: str


class ThoughtIngestRequest(BaseModel):
    content: Annotated[str, Field(min_length=1, max_length=20000)]

    @field_validator("content")
    @classmethod
    def content_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("content must not be blank")
        return v


class ThoughtIngestResponse(BaseModel):
    success: bool
    thought_id: str
    summary: str
    category: str
    confidence: float
    keywords: List[str]
    linked_thought_ids: List[str]


class AgentRunRequest(BaseModel):
    task: Annotated[str, Field(min_length=1, max_length=8000)]
    session_id: Optional[Annotated[str, Field(pattern=r'^[A-Za-z0-9._:\-]+$')]] = None

    @field_validator("task")
    @classmethod
    def task_step_count(cls, v: str) -> str:
        step_count = len(v.split(" Then "))
        if step_count > _MAX_TASK_STEPS:
            raise ValueError(f"task exceeds max step count ({_MAX_TASK_STEPS})")
        return v


class AgentRunResponse(BaseModel):
    session_id: str
    result: str
    steps: List[Dict[str, Any]]
    tokens_used: int
    cost: float


class TimelineResponse(BaseModel):
    events: List[Dict[str, Any]]


class TokenUsageResponse(BaseModel):
    total: float
    by_session: Dict[str, float]


class SwarmTaskRequest(BaseModel):
    task: Annotated[str, Field(min_length=1, max_length=8000)]
    agent_type: Annotated[str, Field(min_length=1, max_length=64)]
    priority: str = "normal"
    payload: Optional[Dict[str, Any]] = None
    workflow_id: Optional[str] = None
    complexity: str = "medium"

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        v2 = v.lower().strip()
        if v2 not in {"high", "normal", "low"}:
            raise ValueError("priority must be one of: high, normal, low")
        return v2

    @field_validator("complexity")
    @classmethod
    def validate_complexity(cls, v: str) -> str:
        v2 = v.lower().strip()
        if v2 not in {"low", "medium", "high"}:
            raise ValueError("complexity must be one of: low, medium, high")
        return v2


class SwarmTaskResponse(BaseModel):
    success: bool
    task_id: str
    queue: str
    event_id: str


class SwarmConfigResponse(BaseModel):
    min_workers: int
    max_workers: int
    max_tokens_per_min: int
    max_cpu_percent: float
    idle_timeout_seconds: int


class SwarmConfigUpdateRequest(BaseModel):
    min_workers: Optional[int] = None
    max_workers: Optional[int] = None
    max_tokens_per_min: Optional[int] = None
    max_cpu_percent: Optional[float] = None
    idle_timeout_seconds: Optional[int] = None


class SwarmStatusResponse(BaseModel):
    queue_depth: Dict[str, int]
    queue_depth_total: int
    active_workers: int
    desired_workers: int
    guardrails: Dict[str, Any]
    config: SwarmConfigResponse


class SwarmEventItem(BaseModel):
    event_id: str
    type: str
    timestamp: str
    workflow_id: Optional[str] = None
    task_id: Optional[str] = None
    agent_type: Optional[str] = None
    priority: Optional[str] = None
    payload: Dict[str, Any]
    trace_id: str


class SwarmEventsResponse(BaseModel):
    events: List[SwarmEventItem]


class SwarmScalerTickResponse(BaseModel):
    desired_workers: int
    active_workers: int
    queue_depth_total: int
    frozen_scale_up: bool
    reason: Optional[str] = None


class MemoryLearnRequest(BaseModel):
    source_model: Annotated[str, Field(min_length=1, max_length=80)]
    topic: Annotated[str, Field(min_length=1, max_length=140)]
    details: Annotated[str, Field(min_length=1, max_length=20000)]
    impact_level: str = "low"
    confidence: float = 0.7
    tags: Optional[List[str]] = None

    @field_validator("impact_level")
    @classmethod
    def validate_impact_level(cls, v: str) -> str:
        v2 = v.lower().strip()
        if v2 not in {"low", "medium", "high"}:
            raise ValueError("impact_level must be one of: low, medium, high")
        return v2

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if v < 0 or v > 1:
            raise ValueError("confidence must be between 0 and 1")
        return v


class MemoryFeedItem(BaseModel):
    id: str
    source_model: str
    topic: str
    details: str
    impact_level: str
    confidence: float
    tags: List[str]
    created_at: str


class MemoryLearnResponse(BaseModel):
    success: bool
    item: MemoryFeedItem


class MemoryFeedResponse(BaseModel):
    items: List[MemoryFeedItem]


class WorkflowHpoTerm(BaseModel):
    id: Annotated[str, Field(min_length=3, max_length=32)]
    label: Annotated[str, Field(min_length=1, max_length=200)]
    confidence: float = Field(ge=0.0, le=1.0)


class WorkflowTopCandidate(BaseModel):
    chr: Annotated[str, Field(min_length=1, max_length=32)]
    pos: int = Field(ge=1)
    ref: Annotated[str, Field(min_length=1, max_length=64)]
    alt: Annotated[str, Field(min_length=1, max_length=64)]
    quality: float = Field(ge=0.0)
    depth: int = Field(ge=0)
    pathogenicityScore: float = Field(ge=0.0, le=1.0)
    phenotypeRelevance: float = Field(ge=0.0, le=1.0)
    combinedScore: float = Field(ge=0.0, le=1.0)


class WorkflowDiagnosis(BaseModel):
    topCandidate: WorkflowTopCandidate
    candidateGenes: List[Annotated[str, Field(min_length=1, max_length=64)]]
    hpoTerms: List[WorkflowHpoTerm]
    interpretation: Annotated[str, Field(min_length=1, max_length=20000)]


class MedicalWorkflowLearnRequest(BaseModel):
    workflowId: Annotated[str, Field(min_length=1, max_length=120)]
    patientId: Optional[Annotated[str, Field(min_length=1, max_length=120)]] = None
    diagnosis: WorkflowDiagnosis
    confidence: float = Field(ge=0.0, le=1.0)
    duration: int = Field(ge=0)
    source_model: Annotated[str, Field(min_length=1, max_length=80)] = "genomics-platform"


class MedicalWorkflowLearnResponse(BaseModel):
    success: bool
    workflow_id: str
    patient_ref: str
    item: MemoryFeedItem


class MemoryInjectPreviewRequest(BaseModel):
    session_id: Optional[Annotated[str, Field(pattern=r'^[A-Za-z0-9._:\-]+$')]] = None
    agent_type: Optional[Annotated[str, Field(min_length=1, max_length=64)]] = None
    domain: Optional[Annotated[str, Field(min_length=1, max_length=64)]] = None
    layers: Optional[List[Annotated[str, Field(min_length=1, max_length=64)]]] = None
    impact_levels: Optional[List[str]] = None
    min_confidence: float = 0.0
    query: Optional[Annotated[str, Field(min_length=1, max_length=200)]] = None
    max_items: int = 10

    @field_validator("min_confidence")
    @classmethod
    def validate_min_confidence(cls, v: float) -> float:
        if v < 0 or v > 1:
            raise ValueError("min_confidence must be between 0 and 1")
        return v

    @field_validator("impact_levels")
    @classmethod
    def validate_impact_levels(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        normalized = [item.lower().strip() for item in v if item and item.strip()]
        allowed = {"low", "medium", "high"}
        invalid = [item for item in normalized if item not in allowed]
        if invalid:
            raise ValueError("impact_levels must only include: low, medium, high")
        return normalized

    @field_validator("max_items")
    @classmethod
    def validate_max_items(cls, v: int) -> int:
        if v < 1 or v > _MEMORY_INJECTION_MAX_ITEMS:
            raise ValueError(f"max_items must be between 1 and {_MEMORY_INJECTION_MAX_ITEMS}")
        return v


class MemoryInjectCandidate(BaseModel):
    item: MemoryFeedItem
    score: float
    reasons: List[str]


class MemoryInjectPreviewResponse(BaseModel):
    success: bool
    session_id: str
    filters: Dict[str, Any]
    candidates: List[MemoryInjectCandidate]


class MemoryInjectApplyRequest(BaseModel):
    session_id: Annotated[str, Field(pattern=r'^[A-Za-z0-9._:\-]+$')]
    selected_item_ids: Optional[List[Annotated[str, Field(min_length=1, max_length=128)]]] = None
    agent_type: Optional[Annotated[str, Field(min_length=1, max_length=64)]] = None
    domain: Optional[Annotated[str, Field(min_length=1, max_length=64)]] = None
    layers: Optional[List[Annotated[str, Field(min_length=1, max_length=64)]]] = None
    impact_levels: Optional[List[str]] = None
    min_confidence: float = 0.0
    query: Optional[Annotated[str, Field(min_length=1, max_length=200)]] = None
    max_items: int = 10

    @field_validator("min_confidence")
    @classmethod
    def validate_apply_min_confidence(cls, v: float) -> float:
        if v < 0 or v > 1:
            raise ValueError("min_confidence must be between 0 and 1")
        return v

    @field_validator("impact_levels")
    @classmethod
    def validate_apply_impact_levels(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        normalized = [item.lower().strip() for item in v if item and item.strip()]
        allowed = {"low", "medium", "high"}
        invalid = [item for item in normalized if item not in allowed]
        if invalid:
            raise ValueError("impact_levels must only include: low, medium, high")
        return normalized

    @field_validator("max_items")
    @classmethod
    def validate_apply_max_items(cls, v: int) -> int:
        if v < 1 or v > _MEMORY_INJECTION_MAX_ITEMS:
            raise ValueError(f"max_items must be between 1 and {_MEMORY_INJECTION_MAX_ITEMS}")
        return v


class MemoryInjectApplyResponse(BaseModel):
    success: bool
    session_id: str
    applied_count: int
    applied_item_ids: List[str]
    injected_at: str


# ============== HEALTH ENDPOINTS ==============


def _health_payload() -> HealthResponse:
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow().isoformat(),
        service="snac-backend",
        services={
            "openai": "configured" if OPENAI_API_KEY else "missing",
            "qdrant": f"{QDRANT_HOST}:{QDRANT_PORT}",
            "redis": f"{REDIS_HOST}:{REDIS_PORT}",
        }
    )

@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint."""
    return _health_payload()


@app.get("/health", response_model=HealthResponse)
async def health():
    """Alternate health check with consistent payload."""
    return _health_payload()


@app.get("/api/health", response_model=HealthResponse)
async def api_health():
    """Health endpoint that remains valid when API is reverse-proxied under /api."""
    return _health_payload()


@app.get("/status", response_model=HealthResponse)
async def status():
    """Simple text-friendly status endpoint for scripts and monitors."""
    return _health_payload()


# ============== INGEST ENDPOINT ==============

@app.post("/ingest", response_model=IngestResponse)
async def ingest_document(request: IngestRequest, background_tasks: BackgroundTasks):
    """
    Ingest document into the RAG system.
    Chunks content, generates embeddings (requires OpenAI key), and stores in Qdrant.
    """
    import uuid

    if _qdrant is None or _openai_client is None:
        raise HTTPException(
            status_code=503,
            detail="RAG unavailable: Qdrant or OpenAI not configured"
        )

    document_id = str(uuid.uuid4())
    chunk_size = 500
    chunks = [request.content[i:i + chunk_size]
              for i in range(0, len(request.content), chunk_size)]

    failed_chunks: List[int] = []
    for idx, chunk in enumerate(chunks):
        try:
            embedding = await _embed(chunk)
            await _qdrant.upsert(
                collection_name=QDRANT_COLLECTION,
                points=[PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload={
                        "text": chunk,
                        "doc_id": document_id,
                        "chunk_index": idx,
                        **(request.metadata or {}),
                    }
                )]
            )
        except Exception as e:
            print(f"Qdrant upsert error chunk {idx}: {_redact_secrets(str(e))}")
            failed_chunks.append(idx)

    if failed_chunks:
        raise HTTPException(
            status_code=502,
            detail=f"Partial ingest failure: {len(failed_chunks)}/{len(chunks)} chunks failed "
                   f"(indices: {failed_chunks})"
        )

    await _timeline_append({
        "type": "ingest",
        "document_id": document_id,
        "chunks": len(chunks),
        "timestamp": datetime.utcnow().isoformat(),
        "metadata": request.metadata or {}
    })

    return IngestResponse(
        success=True,
        chunks=len(chunks),
        document_id=document_id
    )


@app.post("/ingest-thought", response_model=ThoughtIngestResponse)
async def ingest_thought(request: ThoughtIngestRequest):
    """Ingest a raw thought and auto-structure it into summary, category, and links."""
    import uuid

    thought_id = str(uuid.uuid4())
    content = request.content.strip()
    keywords = _extract_keywords(content)
    category, confidence = _classify_thought(content, keywords)
    summary = _summarize_thought(content)

    existing = await _thought_recent(limit=300)
    linked_thought_ids = _find_related_thought_ids(keywords, existing)

    thought_entry = {
        "id": thought_id,
        "content": content,
        "summary": summary,
        "category": category,
        "confidence": confidence,
        "keywords": keywords,
        "linked_thought_ids": linked_thought_ids,
        "created_at": datetime.utcnow().isoformat(),
    }
    await _thought_add(thought_entry)

    await _timeline_append({
        "type": "thought_ingest",
        "thought_id": thought_id,
        "summary": summary,
        "category": category,
        "linked_count": len(linked_thought_ids),
        "timestamp": datetime.utcnow().isoformat(),
    })

    return ThoughtIngestResponse(
        success=True,
        thought_id=thought_id,
        summary=summary,
        category=category,
        confidence=confidence,
        keywords=keywords,
        linked_thought_ids=linked_thought_ids,
    )


# ============== SWARM ENDPOINTS ==============

@app.post("/swarm/task", response_model=SwarmTaskResponse)
async def swarm_enqueue_task(request: SwarmTaskRequest):
    import uuid

    task_id = str(uuid.uuid4())
    workflow_id = request.workflow_id or str(uuid.uuid4())
    trace_id = str(uuid.uuid4())

    task_entry = {
        "task_id": task_id,
        "workflow_id": workflow_id,
        "task": request.task,
        "agent_type": request.agent_type,
        "priority": request.priority,
        "payload": request.payload or {},
        "complexity": request.complexity,
        "status": "queued",
        "created_at": datetime.utcnow().isoformat(),
    }
    await _swarm_enqueue_task(task_entry, request.priority)

    event = await _swarm_emit_event(
        "swarm.task.created",
        workflow_id=workflow_id,
        task_id=task_id,
        agent_type=request.agent_type,
        priority=request.priority,
        payload={
            "complexity": request.complexity,
            "task_preview": request.task[:120],
        },
        trace_id=trace_id,
    )

    await _timeline_append({
        "type": "swarm_task_created",
        "task_id": task_id,
        "agent_type": request.agent_type,
        "priority": request.priority,
        "timestamp": datetime.utcnow().isoformat(),
    })

    return SwarmTaskResponse(success=True, task_id=task_id, queue=request.priority, event_id=event["event_id"])


@app.get("/swarm/status", response_model=SwarmStatusResponse)
async def swarm_status():
    data = await _swarm_calculate_desired_workers()
    return SwarmStatusResponse(
        queue_depth=data["queue_depth"],
        queue_depth_total=data["queue_depth_total"],
        active_workers=data["active_workers"],
        desired_workers=data["desired_workers"],
        guardrails=data["guardrails"],
        config=SwarmConfigResponse(**data["config"]),
    )


@app.post("/swarm/scaler/tick", response_model=SwarmScalerTickResponse)
async def swarm_scaler_tick():
    data = await _swarm_calculate_desired_workers()

    await _swarm_emit_event(
        "swarm.scaler.decision",
        payload={
            "queue_depth_total": data["queue_depth_total"],
            "active_workers": data["active_workers"],
            "desired_workers": data["desired_workers"],
            "frozen_scale_up": data["frozen_scale_up"],
            "reason": data["reason"],
        },
    )

    await _timeline_append({
        "type": "swarm_scaler_decision",
        "queue_depth_total": data["queue_depth_total"],
        "desired_workers": data["desired_workers"],
        "active_workers": data["active_workers"],
        "timestamp": datetime.utcnow().isoformat(),
    })

    return SwarmScalerTickResponse(
        desired_workers=data["desired_workers"],
        active_workers=data["active_workers"],
        queue_depth_total=data["queue_depth_total"],
        frozen_scale_up=data["frozen_scale_up"],
        reason=data["reason"],
    )


@app.get("/swarm/events/recent", response_model=SwarmEventsResponse)
async def swarm_events_recent(limit: int = 50):
    limit = max(1, min(limit, 500))
    events = await _swarm_recent_events(limit=limit)
    return SwarmEventsResponse(events=[SwarmEventItem(**e) for e in events])


@app.post("/swarm/config", response_model=SwarmConfigResponse)
async def swarm_update_config(request: SwarmConfigUpdateRequest):
    current = await _swarm_get_config()
    update_data = request.model_dump(exclude_none=True)
    merged = {**current, **update_data}

    if merged["min_workers"] < 0 or merged["max_workers"] < 1:
        raise HTTPException(status_code=400, detail="invalid worker limits")
    if merged["min_workers"] > merged["max_workers"]:
        raise HTTPException(status_code=400, detail="min_workers cannot exceed max_workers")
    if merged["max_tokens_per_min"] < 1:
        raise HTTPException(status_code=400, detail="max_tokens_per_min must be >= 1")
    if merged["max_cpu_percent"] <= 0 or merged["max_cpu_percent"] > 100:
        raise HTTPException(status_code=400, detail="max_cpu_percent must be in (0, 100]")
    if merged["idle_timeout_seconds"] < 1:
        raise HTTPException(status_code=400, detail="idle_timeout_seconds must be >= 1")

    await _swarm_set_config(merged)
    await _swarm_emit_event("swarm.config.updated", payload=merged)
    return SwarmConfigResponse(**merged)


@app.post("/memory/learn", response_model=MemoryLearnResponse)
async def memory_learn(request: MemoryLearnRequest):
    import uuid

    item = {
        "id": str(uuid.uuid4()),
        "source_model": request.source_model.strip(),
        "topic": request.topic.strip(),
        "details": request.details.strip(),
        "impact_level": request.impact_level,
        "confidence": request.confidence,
        "tags": request.tags or [],
        "created_at": datetime.utcnow().isoformat(),
    }
    await _memory_knowledge_add(item)

    await _timeline_append({
        "type": "memory_learn",
        "memory_id": item["id"],
        "source_model": item["source_model"],
        "topic": item["topic"],
        "impact_level": item["impact_level"],
        "timestamp": datetime.utcnow().isoformat(),
    })

    return MemoryLearnResponse(success=True, item=MemoryFeedItem(**item))


@app.get("/memory/feed", response_model=MemoryFeedResponse)
async def memory_feed(limit: int = 50):
    limit = max(1, min(limit, 500))
    items = await _memory_knowledge_recent(limit=limit)
    return MemoryFeedResponse(items=[MemoryFeedItem(**i) for i in items])


@app.post("/memory/workflow/learn", response_model=MedicalWorkflowLearnResponse)
async def memory_workflow_learn(request: MedicalWorkflowLearnRequest):
    import uuid

    patient_ref = _anonymize_identifier(request.patientId or "unknown")
    top = request.diagnosis.topCandidate
    lead_gene = request.diagnosis.candidateGenes[0] if request.diagnosis.candidateGenes else "unknown"
    hpo_labels = ", ".join([term.label for term in request.diagnosis.hpoTerms[:5]])

    impact_level = "low"
    if request.confidence >= 0.85:
        impact_level = "high"
    elif request.confidence >= 0.7:
        impact_level = "medium"

    details = (
        f"workflow_id: {request.workflowId}\n"
        f"patient_ref: {patient_ref}\n"
        f"duration_ms: {request.duration}\n"
        f"confidence: {request.confidence:.3f}\n"
        f"top_candidate: {top.chr}:{top.pos} {top.ref}>{top.alt}\n"
        f"combined_score: {top.combinedScore:.4f}\n"
        f"lead_gene: {lead_gene}\n"
        f"candidate_genes: {', '.join(request.diagnosis.candidateGenes[:10])}\n"
        f"hpo_terms: {hpo_labels}\n"
        f"interpretation: {request.diagnosis.interpretation.strip()}"
    )

    item = {
        "id": str(uuid.uuid4()),
        "source_model": request.source_model.strip(),
        "topic": f"Rare disease diagnostic {request.workflowId}",
        "details": details,
        "impact_level": impact_level,
        "confidence": request.confidence,
        "tags": [
            "medical",
            "workflow",
            "rare-disease",
            "diagnostic",
            f"gene:{lead_gene.lower()}",
        ],
        "created_at": datetime.utcnow().isoformat(),
    }
    await _memory_knowledge_add(item)

    await _timeline_append({
        "type": "memory_workflow_learn",
        "memory_id": item["id"],
        "workflow_id": request.workflowId,
        "patient_ref": patient_ref,
        "confidence": request.confidence,
        "duration_ms": request.duration,
        "timestamp": datetime.utcnow().isoformat(),
    })

    return MedicalWorkflowLearnResponse(
        success=True,
        workflow_id=request.workflowId,
        patient_ref=patient_ref,
        item=MemoryFeedItem(**item),
    )


@app.post("/memory/inject/preview", response_model=MemoryInjectPreviewResponse)
async def memory_inject_preview(request: MemoryInjectPreviewRequest):
    session_id = request.session_id or "global"
    candidates = await _memory_build_injection_candidates(
        session_id=session_id,
        agent_type=request.agent_type,
        domain=request.domain,
        layers=request.layers,
        impact_levels=request.impact_levels,
        min_confidence=request.min_confidence,
        query=request.query,
        max_items=request.max_items,
    )
    return MemoryInjectPreviewResponse(
        success=True,
        session_id=session_id,
        filters={
            "agent_type": request.agent_type,
            "domain": request.domain,
            "layers": request.layers or [],
            "impact_levels": request.impact_levels or [],
            "min_confidence": request.min_confidence,
            "query": request.query,
            "max_items": request.max_items,
        },
        candidates=[MemoryInjectCandidate(**item) for item in candidates],
    )


@app.post("/memory/inject/apply", response_model=MemoryInjectApplyResponse)
async def memory_inject_apply(request: MemoryInjectApplyRequest):
    recent_items = await _memory_knowledge_recent(limit=max(_MEMORY_INJECTION_MAX_ITEMS * 5, 200))
    recent_by_id = {str(item.get("id")): item for item in recent_items if item.get("id")}

    selected: List[Dict[str, Any]] = []
    if request.selected_item_ids:
        for item_id in request.selected_item_ids:
            item = recent_by_id.get(item_id)
            if item:
                selected.append(item)
    else:
        candidates = await _memory_build_injection_candidates(
            session_id=request.session_id,
            agent_type=request.agent_type,
            domain=request.domain,
            layers=request.layers,
            impact_levels=request.impact_levels,
            min_confidence=request.min_confidence,
            query=request.query,
            max_items=request.max_items,
        )
        selected = [candidate["item"].model_dump() for candidate in candidates]

    selected = selected[:request.max_items]
    injected_at = datetime.utcnow().isoformat()

    memory_injection_runtime[request.session_id] = {
        "session_id": request.session_id,
        "agent_type": request.agent_type,
        "domain": request.domain,
        "layers": request.layers or [],
        "impact_levels": request.impact_levels or [],
        "min_confidence": request.min_confidence,
        "query": request.query,
        "max_items": request.max_items,
        "items": selected,
        "item_ids": [str(item.get("id")) for item in selected if item.get("id")],
        "injected_at": injected_at,
    }

    await _timeline_append({
        "type": "memory_injection_apply",
        "session_id": request.session_id,
        "applied_count": len(selected),
        "item_ids": [str(item.get("id")) for item in selected if item.get("id")][:10],
        "domain": request.domain,
        "agent_type": request.agent_type,
        "timestamp": datetime.utcnow().isoformat(),
    })

    return MemoryInjectApplyResponse(
        success=True,
        session_id=request.session_id,
        applied_count=len(selected),
        applied_item_ids=[str(item.get("id")) for item in selected if item.get("id")],
        injected_at=injected_at,
    )


# ============== STORAGE HELPERS (Redis-backed with in-memory fallback) ==============

async def _session_exists(session_id: str) -> bool:
    if _redis:
        return bool(await _redis.exists(f"session:{session_id}"))
    return session_id in agent_sessions


async def _session_get(session_id: str) -> Optional[Dict]:
    if _redis:
        data = await _redis.get(f"session:{session_id}")
        return json.loads(data) if data else None
    return agent_sessions.get(session_id)


async def _session_set(session_id: str, data: Dict) -> None:
    if _redis:
        await _redis.set(f"session:{session_id}", json.dumps(data), ex=86400)
    else:
        agent_sessions[session_id] = data
        _fallback_session_last_seen[session_id] = time.time()
        _prune_memory_fallback_state()


async def _session_delete(session_id: str) -> None:
    if _redis:
        await _redis.delete(f"session:{session_id}")
        await _redis.hdel("token_usage", f"session:{session_id}")
    else:
        agent_sessions.pop(session_id, None)
        token_usage["by_session"].pop(session_id, None)
        _fallback_session_last_seen.pop(session_id, None)


async def _timeline_append(event: Dict) -> None:
    if _redis:
        await _redis.rpush("timeline", json.dumps(event))
        await _redis.ltrim("timeline", -10000, -1)
    else:
        memory_timeline.append(event)
        _prune_memory_fallback_state()


async def _timeline_get(limit: int = 50) -> List[Dict]:
    if _redis:
        items = await _redis.lrange("timeline", -limit, -1)
        return [json.loads(i) for i in items]
    return memory_timeline[-limit:]


async def _timeline_get_session(session_id: str) -> List[Dict]:
    # Scans full timeline; replace with per-session key for high-volume use
    if _redis:
        items = await _redis.lrange("timeline", 0, -1)
        decoded = [json.loads(i) for i in items]
        return [e for e in decoded if e.get("session_id") == session_id]
    return [e for e in memory_timeline if e.get("session_id") == session_id]


async def _token_incr(session_id: str, cost: float) -> None:
    if _redis:
        await _redis.hincrbyfloat("token_usage", "total", cost)
        await _redis.hincrbyfloat("token_usage", f"session:{session_id}", cost)
    else:
        token_usage["total"] += cost
        token_usage["by_session"][session_id] = token_usage["by_session"].get(session_id, 0.0) + cost
        _prune_memory_fallback_state()


async def _token_get() -> Dict[str, Any]:
    if _redis:
        raw = await _redis.hgetall("token_usage")
        return {
            "total": float(raw.get("total", 0)),
            "by_session": {
                k.replace("session:", ""): float(v)
                for k, v in raw.items()
                if k.startswith("session:")
            },
        }
    return token_usage


async def _thought_add(thought: Dict[str, Any]) -> None:
    if _redis:
        await _redis.rpush("thoughts", json.dumps(thought))
        await _redis.ltrim("thoughts", -_MEMORY_FALLBACK_MAX_THOUGHTS, -1)
    else:
        thought_memory.append(thought)
        _prune_memory_fallback_state()


async def _thought_recent(limit: int = 250) -> List[Dict[str, Any]]:
    if _redis:
        items = await _redis.lrange("thoughts", -limit, -1)
        return [json.loads(i) for i in items]
    return thought_memory[-limit:]


async def _memory_knowledge_add(entry: Dict[str, Any]) -> None:
    if _redis:
        await _redis.rpush(_MEMORY_SHARED_KNOWLEDGE_KEY, json.dumps(entry))
        await _redis.ltrim(_MEMORY_SHARED_KNOWLEDGE_KEY, -_MEMORY_FALLBACK_MAX_SHARED_KNOWLEDGE, -1)
    else:
        shared_knowledge_memory.append(entry)
        _prune_memory_fallback_state()


async def _memory_knowledge_recent(limit: int = 50) -> List[Dict[str, Any]]:
    if _redis:
        items = await _redis.lrange(_MEMORY_SHARED_KNOWLEDGE_KEY, -limit, -1)
        return [json.loads(i) for i in items]
    return shared_knowledge_memory[-limit:]


def _memory_item_tags(item: Dict[str, Any]) -> List[str]:
    return [str(tag).strip().lower() for tag in (item.get("tags") or []) if str(tag).strip()]


def _memory_filter_tag_match(tags: List[str], needle: str, prefix: Optional[str] = None) -> bool:
    value = needle.strip().lower()
    if not value:
        return False
    if value in tags:
        return True
    if prefix and f"{prefix}:{value}" in tags:
        return True
    return False


def _memory_matches_layers(tags: List[str], layers: Optional[List[str]]) -> bool:
    if not layers:
        return True
    normalized = [layer.strip().lower() for layer in layers if layer and layer.strip()]
    if not normalized:
        return True
    return any(_memory_filter_tag_match(tags, layer, "layer") for layer in normalized)


async def _memory_build_injection_candidates(
    *,
    session_id: str,
    agent_type: Optional[str],
    domain: Optional[str],
    layers: Optional[List[str]],
    impact_levels: Optional[List[str]],
    min_confidence: float,
    query: Optional[str],
    max_items: int,
) -> List[Dict[str, Any]]:
    items = await _memory_knowledge_recent(limit=max(_MEMORY_INJECTION_MAX_ITEMS * 5, 200))
    impact_set = set(impact_levels or [])
    query_norm = (query or "").strip().lower()

    scored: List[Dict[str, Any]] = []
    for raw in reversed(items):
        topic = str(raw.get("topic") or "")
        details = str(raw.get("details") or "")
        impact = str(raw.get("impact_level") or "low").lower().strip()
        confidence = float(raw.get("confidence") or 0.0)
        tags = _memory_item_tags(raw)
        blob = (topic + "\n" + details).lower()

        if impact_set and impact not in impact_set:
            continue
        if confidence < min_confidence:
            continue
        if domain and not (
            _memory_filter_tag_match(tags, domain, "domain")
            or domain.lower().strip() in blob
        ):
            continue
        if agent_type and not (
            _memory_filter_tag_match(tags, agent_type, "agent")
            or agent_type.lower().strip() in blob
        ):
            continue
        if not _memory_matches_layers(tags, layers):
            continue
        if query_norm and query_norm not in blob:
            continue

        score = confidence * 0.7
        score += {"low": 0.08, "medium": 0.16, "high": 0.24}.get(impact, 0.05)
        reasons: List[str] = [f"confidence={confidence:.2f}", f"impact={impact}"]

        if query_norm:
            if query_norm in topic.lower():
                score += 0.2
                reasons.append("topic_query_match")
            elif query_norm in details.lower():
                score += 0.1
                reasons.append("details_query_match")

        if domain and _memory_filter_tag_match(tags, domain, "domain"):
            score += 0.06
            reasons.append("domain_tag_match")

        if agent_type and _memory_filter_tag_match(tags, agent_type, "agent"):
            score += 0.06
            reasons.append("agent_tag_match")

        if layers:
            score += 0.03
            reasons.append("layer_match")

        scored.append({
            "item": MemoryFeedItem(**raw),
            "score": round(score, 4),
            "reasons": reasons,
        })

    scored.sort(key=lambda entry: entry["score"], reverse=True)
    return scored[:max_items]


def _extract_keywords(text: str, limit: int = 8) -> List[str]:
    stopwords = {
        "the", "and", "for", "that", "with", "this", "from", "then", "into", "have", "your",
        "about", "when", "where", "what", "will", "just", "idea", "thought", "link", "might",
    }
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", text.lower())
    freq: Dict[str, int] = {}
    for w in words:
        if w in stopwords:
            continue
        freq[w] = freq.get(w, 0) + 1
    ordered = sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))
    return [w for w, _ in ordered[:limit]]


def _anonymize_identifier(value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return f"anon-{digest[:12]}"


def _classify_thought(content: str, keywords: List[str]) -> tuple[str, float]:
    text = (content + " " + " ".join(keywords)).lower()
    rulebook = {
        "AI_SYSTEMS": ["agent", "agents", "llm", "ai", "prompt", "model", "reasoning"],
        "AUTOMATION": ["workflow", "n8n", "pipeline", "automation", "orchestrator", "trigger"],
        "INFRASTRUCTURE": ["docker", "nginx", "redis", "postgres", "qdrant", "deploy", "vps"],
        "RESEARCH": ["paper", "arxiv", "study", "experiment", "benchmark", "hypothesis"],
        "BUSINESS": ["customer", "pricing", "revenue", "market", "sales", "offer"],
        "CRYPTO": ["crypto", "wallet", "token", "blockchain", "defi", "chain"],
    }

    best_category = "AI_SYSTEMS"
    best_hits = 0
    for category, needles in rulebook.items():
        hits = sum(1 for needle in needles if needle in text)
        if hits > best_hits:
            best_hits = hits
            best_category = category

    confidence = min(0.99, 0.55 + (best_hits * 0.1))
    return best_category, round(confidence, 2)


def _summarize_thought(content: str, max_len: int = 180) -> str:
    compact = re.sub(r"\s+", " ", content.strip())
    if len(compact) <= max_len:
        return compact
    return compact[: max_len - 1].rstrip() + "..."


def _overlap_score(a: List[str], b: List[str]) -> int:
    return len(set(a) & set(b))


def _find_related_thought_ids(current_keywords: List[str], existing: List[Dict[str, Any]], limit: int = 5) -> List[str]:
    scored: List[tuple[int, str]] = []
    for thought in existing:
        tid = thought.get("id")
        kws = thought.get("keywords") or []
        if not tid:
            continue
        score = _overlap_score(current_keywords, kws)
        if score > 0:
            scored.append((score, str(tid)))
    scored.sort(key=lambda s: (-s[0], s[1]))
    return [tid for _, tid in scored[:limit]]


def _swarm_queue_key(priority: str) -> str:
    return f"{_SWARM_QUEUE_KEY_PREFIX}:{priority}"


async def _swarm_get_config() -> Dict[str, Any]:
    if _redis:
        raw = await _redis.hgetall(_SWARM_CONFIG_KEY)
        if not raw:
            return dict(swarm_config)
        return {
            "min_workers": int(raw.get("min_workers", swarm_config["min_workers"])),
            "max_workers": int(raw.get("max_workers", swarm_config["max_workers"])),
            "max_tokens_per_min": int(raw.get("max_tokens_per_min", swarm_config["max_tokens_per_min"])),
            "max_cpu_percent": float(raw.get("max_cpu_percent", swarm_config["max_cpu_percent"])),
            "idle_timeout_seconds": int(raw.get("idle_timeout_seconds", swarm_config["idle_timeout_seconds"])),
        }
    return dict(swarm_config)


async def _swarm_set_config(config: Dict[str, Any]) -> None:
    if _redis:
        await _redis.hset(_SWARM_CONFIG_KEY, mapping={
            "min_workers": str(config["min_workers"]),
            "max_workers": str(config["max_workers"]),
            "max_tokens_per_min": str(config["max_tokens_per_min"]),
            "max_cpu_percent": str(config["max_cpu_percent"]),
            "idle_timeout_seconds": str(config["idle_timeout_seconds"]),
        })
    else:
        swarm_config.update(config)


async def _swarm_emit_event(
    event_type: str,
    *,
    payload: Optional[Dict[str, Any]] = None,
    workflow_id: Optional[str] = None,
    task_id: Optional[str] = None,
    agent_type: Optional[str] = None,
    priority: Optional[str] = None,
    trace_id: Optional[str] = None,
) -> Dict[str, Any]:
    import uuid

    event = {
        "event_id": str(uuid.uuid4()),
        "type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "workflow_id": workflow_id,
        "task_id": task_id,
        "agent_type": agent_type,
        "priority": priority,
        "payload": payload or {},
        "trace_id": trace_id or str(uuid.uuid4()),
    }

    if _redis:
        await _redis.rpush(_SWARM_EVENTS_KEY, json.dumps(event))
        await _redis.ltrim(_SWARM_EVENTS_KEY, -_MEMORY_FALLBACK_MAX_SWARM_EVENTS, -1)
    else:
        swarm_events.append(event)
        _prune_memory_fallback_state()
    return event


async def _swarm_recent_events(limit: int = 50) -> List[Dict[str, Any]]:
    if _redis:
        items = await _redis.lrange(_SWARM_EVENTS_KEY, -limit, -1)
        return [json.loads(i) for i in items]
    return swarm_events[-limit:]


async def _swarm_queue_depth() -> Dict[str, int]:
    if _redis:
        high = await _redis.llen(_swarm_queue_key("high"))
        normal = await _redis.llen(_swarm_queue_key("normal"))
        low = await _redis.llen(_swarm_queue_key("low"))
        return {"high": int(high), "normal": int(normal), "low": int(low)}
    return {
        "high": len(swarm_state.get("queue_high", [])),
        "normal": len(swarm_state.get("queue_normal", [])),
        "low": len(swarm_state.get("queue_low", [])),
    }


async def _swarm_active_workers_count() -> int:
    if _redis:
        return int(await _redis.hlen(_SWARM_WORKERS_ACTIVE_KEY))
    return len(swarm_state.get("active_workers", {}))


async def _swarm_enqueue_task(task_entry: Dict[str, Any], priority: str) -> None:
    if _redis:
        await _redis.rpush(_swarm_queue_key(priority), json.dumps(task_entry))
    else:
        key = f"queue_{priority}"
        if key not in swarm_state:
            swarm_state[key] = []
        swarm_state[key].append(task_entry)


async def _swarm_calculate_desired_workers() -> Dict[str, Any]:
    config = await _swarm_get_config()
    queue_depth = await _swarm_queue_depth()
    queue_depth_total = queue_depth["high"] + queue_depth["normal"] + queue_depth["low"]
    active_workers = await _swarm_active_workers_count()

    desired = int(math.ceil(queue_depth_total / 2.0))
    desired = max(config["min_workers"], min(config["max_workers"], desired))

    frozen = False
    reason = None
    cpu_percent = 0.0
    tokens_per_min = 0

    if cpu_percent > config["max_cpu_percent"]:
        frozen = True
        reason = "cpu_limit"
    elif tokens_per_min > config["max_tokens_per_min"]:
        frozen = True
        reason = "token_limit"

    if frozen and desired > active_workers:
        desired = active_workers

    return {
        "queue_depth": queue_depth,
        "queue_depth_total": queue_depth_total,
        "active_workers": active_workers,
        "desired_workers": desired,
        "frozen_scale_up": frozen,
        "reason": reason,
        "guardrails": {
            "cpu_percent": cpu_percent,
            "tokens_per_min": tokens_per_min,
            "frozen_scale_up": frozen,
            "reason": reason,
        },
        "config": config,
    }


async def _embed(text: str) -> List[float]:
    """Generate text embedding via OpenAI. Caller must ensure _openai_client is not None."""
    response = await _openai_client.embeddings.create(
        model=OPENAI_EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding


# ============== AGENT RUN ENDPOINT ==============

@app.post("/agent/run", response_model=AgentRunResponse)
async def run_agent(request: AgentRunRequest):
    """
    Run agent task with memory and RAG.
    
    Supports compound tasks like:
    - "QUERY: What is the capital of Japan? Then CALC: 25 * 4"
    - "QUERY: What is 2+2? Then CALC: result * 3"
    """
    import uuid

    session_id = request.session_id or str(uuid.uuid4())

    if not await _session_exists(session_id):
        await _session_set(session_id, {"history": [], "context": {}})

    session = await _session_get(session_id)
    steps = []

    task_parts = _parse_task(request.task)

    await _timeline_append({
        "type": "agent_start",
        "session_id": session_id,
        "task": request.task,
        "timestamp": datetime.utcnow().isoformat()
    })

    for i, part in enumerate(task_parts):
        step_result = await _execute_step(part, session, session_id, step_num=i)
        steps.append(step_result)

        session["context"]["last_result"] = step_result["result"]
        session["history"].append({
            "step": part["type"],
            "input": part["query"],
            "result": step_result["result"]
        })
        await _session_set(session_id, session)

        await _timeline_append({
            "type": "agent_step",
            "session_id": session_id,
            "step": part["type"],
            "result": step_result["result"],
            "timestamp": datetime.utcnow().isoformat()
        })

    tokens_used = sum(s.get("tokens", 0) for s in steps)
    cost = tokens_used * _OPENAI_COST_PER_TOKEN
    await _token_incr(session_id, cost)

    await _timeline_append({
        "type": "agent_complete",
        "session_id": session_id,
        "result": steps[-1]["result"] if steps else "",
        "tokens": tokens_used,
        "cost": cost,
        "timestamp": datetime.utcnow().isoformat()
    })

    return AgentRunResponse(
        session_id=session_id,
        result=steps[-1]["result"] if steps else "",
        steps=steps,
        tokens_used=tokens_used,
        cost=cost
    )


def _parse_task(task: str) -> List[Dict[str, str]]:
    """Parse compound task into steps."""
    parts = task.split(" Then ")
    steps = []
    
    for part in parts:
        part = part.strip()
        if part.startswith("QUERY:"):
            steps.append({"type": "query", "query": part[6:].strip()})
        elif part.startswith("CALC:"):
            steps.append({"type": "calc", "query": part[5:].strip()})
        else:
            # Default to query
            steps.append({"type": "query", "query": part})
    
    return steps


async def _execute_step(
    step: Dict[str, str], 
    session: Dict[str, Any],
    session_id: str,
    step_num: int
) -> Dict[str, Any]:
    """Execute a single agent step."""
    
    tokens = 0
    if step["type"] == "query":
        result, tokens = await _execute_query(step["query"], session)
    elif step["type"] == "calc":
        result = await _execute_calc(step["query"], session)
    else:
        result = f"Unknown step type: {step['type']}"
    
    return {
        "step": step_num + 1,
        "type": step["type"],
        "input": step["query"],
        "result": result,
        "tokens": tokens
    }


async def _execute_query(query: str, session: Dict[str, Any]) -> tuple[str, int]:
    """Execute a natural language query using OpenAI. Returns (response_text, total_tokens)."""

    if _openai_client is None:
        return (f"[MOCK] Query: {query} - Set OPENAI_API_KEY to enable real queries", 0)

    messages: list[dict] = []

    # Inject relevant document context from Qdrant when available
    if _qdrant:
        try:
            query_vec = await _embed(query)
            hits = await _qdrant.search(
                collection_name=QDRANT_COLLECTION,
                query_vector=query_vec,
                limit=3,
            )
            rag_chunks = [h.payload.get("text", "") for h in hits if h.payload]
            if rag_chunks:
                messages.append({
                    "role": "system",
                    "content": "Relevant documents:\n" + "\n---\n".join(rag_chunks),
                })
        except Exception as e:
            print(f"Qdrant search error: {_redact_secrets(str(e))}")

    # Inject recent session history
    if session.get("history"):
        context_lines = "\n".join(
            f"- {h['step']}: {h['result']}" for h in session["history"][-3:]
        )
        messages.append({"role": "system", "content": f"Previous results:\n{context_lines}"})
    messages.append({"role": "user", "content": query})

    try:
        response = await _openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
        )
        text = response.choices[0].message.content or ""
        tokens = response.usage.total_tokens if response.usage else 0
        return (text, tokens)
    except Exception as e:
        print(f"OpenAI query error: {_redact_secrets(str(e))}")
        return ("Error executing query", 0)


async def _execute_calc(calc: str, session: Dict[str, Any]) -> str:
    """Execute a calculation."""
    
    # Handle "result" references
    calc_expr = calc
    if "result" in calc:
        last_result = session.get("context", {}).get("last_result", "")
        # Try to extract numeric value
        nums = re.findall(r'-?\d+\.?\d*', str(last_result))
        if nums:
            calc_expr = calc.replace("result", nums[-1])
    
    try:
        # Parse as AST and evaluate only numeric arithmetic nodes.
        expr = ast.parse(calc_expr, mode="eval")
        result = _safe_eval_ast(expr)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


def _safe_eval_ast(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _safe_eval_ast(node.body)
    if isinstance(node, ast.Num):
        return float(node.n)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp):
        left = _safe_eval_ast(node.left)
        right = _safe_eval_ast(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
        if isinstance(node.op, ast.Mod):
            return left % right
        if isinstance(node.op, ast.Pow):
            return left ** right
        raise ValueError("Unsupported operator")
    if isinstance(node, ast.UnaryOp):
        value = _safe_eval_ast(node.operand)
        if isinstance(node.op, ast.UAdd):
            return +value
        if isinstance(node.op, ast.USub):
            return -value
        raise ValueError("Unsupported unary operator")
    raise ValueError("Only basic arithmetic expressions are allowed")


# ============== MEMORY TIMELINE ==============

@app.get("/memory/timeline", response_model=TimelineResponse)
async def get_timeline(limit: int = 50):
    """Get memory timeline events."""
    return TimelineResponse(events=await _timeline_get(limit))


@app.get("/memory/timeline/{session_id}")
async def get_session_timeline(session_id: str):
    """Get timeline for specific session."""
    events = await _timeline_get_session(session_id)
    return {"session_id": session_id, "events": events}


# ============== TOKEN USAGE ==============

@app.get("/tokens/usage", response_model=TokenUsageResponse)
async def get_token_usage():
    """Get token usage statistics."""
    data = await _token_get()
    return TokenUsageResponse(total=data["total"], by_session=data["by_session"])


# ============== SESSION MANAGEMENT ==============

@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get session state."""
    session = await _session_get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete session and free resources."""
    await _session_delete(session_id)
    return {"success": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
