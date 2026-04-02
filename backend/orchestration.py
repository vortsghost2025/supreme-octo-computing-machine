"""
Autonomous Orchestration Module for SNAC-v2 Backend.

Provides ClusterScheduler, ResourceManager, and AutonomousDecisionEngine
for intelligent task scheduling, resource allocation, and autonomous decisions.
"""

import asyncio
import json
import math
import os
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional


# ============================================================
# ClusterScheduler
# ============================================================


class ClusterScheduler:
    """Manages task scheduling across cluster nodes with priority queues."""

    TASK_STATUSES = {"queued", "scheduled", "running", "completed", "failed", "cancelled"}

    def __init__(self, redis_client=None):
        self._redis = redis_client
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._queue_high: List[str] = []
        self._queue_normal: List[str] = []
        self._queue_low: List[str] = []
        self._lock = asyncio.Lock()

    def _queue_for_priority(self, priority: str) -> List[str]:
        return {
            "high": self._queue_high,
            "normal": self._queue_normal,
            "low": self._queue_low,
        }.get(priority, self._queue_normal)

    async def schedule_task(
        self,
        task: str,
        *,
        priority: str = "normal",
        worker_type: str = "automation_worker",
        payload: Optional[Dict[str, Any]] = None,
        timeout: int = 300,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        task_id = str(uuid.uuid4())
        entry = {
            "task_id": task_id,
            "task": task,
            "priority": priority,
            "worker_type": worker_type,
            "payload": payload or {},
            "timeout": timeout,
            "metadata": metadata or {},
            "status": "queued",
            "created_at": datetime.utcnow().isoformat(),
            "scheduled_at": None,
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None,
        }

        async with self._lock:
            self._tasks[task_id] = entry
            queue = self._queue_for_priority(priority)
            queue.append(task_id)

        if self._redis:
            try:
                await self._redis.hset(
                    "orchestration:tasks", task_id, json.dumps(entry)
                )
                await self._redis.rpush(
                    f"orchestration:queue:{priority}", task_id
                )
            except Exception:
                pass

        return entry

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        if self._redis:
            try:
                raw = await self._redis.hget("orchestration:tasks", task_id)
                if raw:
                    return json.loads(raw)
            except Exception:
                pass
        return self._tasks.get(task_id)

    async def list_tasks(
        self, status: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.get("status") == status]
        tasks.sort(key=lambda t: t.get("created_at", ""), reverse=True)
        return tasks[:limit]

    async def cancel_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return None
            if task["status"] in ("completed", "failed", "cancelled"):
                return task
            task["status"] = "cancelled"
            task["completed_at"] = datetime.utcnow().isoformat()

            for queue in (self._queue_high, self._queue_normal, self._queue_low):
                if task_id in queue:
                    queue.remove(task_id)
                    break

        if self._redis:
            try:
                await self._redis.hset(
                    "orchestration:tasks", task_id, json.dumps(task)
                )
            except Exception:
                pass

        return task

    async def claim_next(self) -> Optional[Dict[str, Any]]:
        async with self._lock:
            for queue in (self._queue_high, self._queue_normal, self._queue_low):
                if queue:
                    task_id = queue.pop(0)
                    task = self._tasks.get(task_id)
                    if task:
                        task["status"] = "scheduled"
                        task["scheduled_at"] = datetime.utcnow().isoformat()
                        return task
        return None

    async def complete_task(
        self, task_id: str, result: Any = None, error: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return None
            task["status"] = "failed" if error else "completed"
            task["completed_at"] = datetime.utcnow().isoformat()
            task["result"] = result
            task["error"] = error

        if self._redis:
            try:
                await self._redis.hset(
                    "orchestration:tasks", task_id, json.dumps(task)
                )
            except Exception:
                pass

        return task

    async def get_stats(self) -> Dict[str, Any]:
        tasks = list(self._tasks.values())
        by_status: Dict[str, int] = {}
        for t in tasks:
            s = t.get("status", "unknown")
            by_status[s] = by_status.get(s, 0) + 1

        return {
            "total_tasks": len(tasks),
            "by_status": by_status,
            "queue_depths": {
                "high": len(self._queue_high),
                "normal": len(self._queue_normal),
                "low": len(self._queue_low),
            },
        }


# ============================================================
# ResourceManager
# ============================================================


class ResourceManager:
    """Tracks and allocates cluster resources (CPU, memory, workers)."""

    def __init__(self, redis_client=None):
        self._redis = redis_client
        self._allocations: Dict[str, Dict[str, Any]] = {}
        self._total_cpu_percent: float = float(
            os.getenv("ORCHESTRATION_TOTAL_CPU", "100")
        )
        self._total_memory_mb: int = int(
            os.getenv("ORCHESTRATION_TOTAL_MEMORY_MB", "4096")
        )
        self._total_workers: int = int(
            os.getenv("ORCHESTRATION_MAX_WORKERS", "12")
        )
        self._lock = asyncio.Lock()

    async def allocate(
        self,
        task_id: str,
        *,
        cpu_percent: float = 10.0,
        memory_mb: int = 256,
        worker_type: str = "automation_worker",
    ) -> Dict[str, Any]:
        allocation = {
            "task_id": task_id,
            "cpu_percent": cpu_percent,
            "memory_mb": memory_mb,
            "worker_type": worker_type,
            "allocated_at": datetime.utcnow().isoformat(),
        }

        async with self._lock:
            self._allocations[task_id] = allocation

        if self._redis:
            try:
                await self._redis.hset(
                    "orchestration:allocations",
                    task_id,
                    json.dumps(allocation),
                )
            except Exception:
                pass

        return allocation

    async def release(self, task_id: str) -> bool:
        async with self._lock:
            removed = self._allocations.pop(task_id, None) is not None

        if self._redis and removed:
            try:
                await self._redis.hdel("orchestration:allocations", task_id)
            except Exception:
                pass

        return removed

    async def get_allocation(self, task_id: str) -> Optional[Dict[str, Any]]:
        return self._allocations.get(task_id)

    async def get_stats(self) -> Dict[str, Any]:
        allocations = list(self._allocations.values())
        used_cpu = sum(a.get("cpu_percent", 0) for a in allocations)
        used_memory = sum(a.get("memory_mb", 0) for a in allocations)

        by_worker_type: Dict[str, int] = {}
        for a in allocations:
            wt = a.get("worker_type", "unknown")
            by_worker_type[wt] = by_worker_type.get(wt, 0) + 1

        return {
            "total_cpu_percent": self._total_cpu_percent,
            "used_cpu_percent": round(used_cpu, 2),
            "available_cpu_percent": round(self._total_cpu_percent - used_cpu, 2),
            "total_memory_mb": self._total_memory_mb,
            "used_memory_mb": used_memory,
            "available_memory_mb": self._total_memory_mb - used_memory,
            "total_workers": self._total_workers,
            "active_allocations": len(allocations),
            "by_worker_type": by_worker_type,
            "cpu_utilization_pct": round(
                (used_cpu / self._total_cpu_percent * 100)
                if self._total_cpu_percent > 0
                else 0,
                1,
            ),
            "memory_utilization_pct": round(
                (used_memory / self._total_memory_mb * 100)
                if self._total_memory_mb > 0
                else 0,
                1,
            ),
        }

    async def can_allocate(
        self, cpu_percent: float = 10.0, memory_mb: int = 256
    ) -> bool:
        stats = await self.get_stats()
        return (
            stats["available_cpu_percent"] >= cpu_percent
            and stats["available_memory_mb"] >= memory_mb
            and stats["active_allocations"] < self._total_workers
        )


# ============================================================
# AutonomousDecisionEngine
# ============================================================


class AutonomousDecisionEngine:
    """Makes autonomous decisions about task routing, scaling, and recovery."""

    DECISION_TYPES = {
        "scale_up",
        "scale_down",
        "reroute",
        "retry",
        "throttle",
        "recover",
        "defer",
    }

    def __init__(self, redis_client=None):
        self._redis = redis_client
        self._decisions: List[Dict[str, Any]] = []
        self._max_decisions = 1000
        self._lock = asyncio.Lock()

    async def make_decision(
        self,
        context: Dict[str, Any],
        *,
        decision_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        if decision_type is None:
            decision_type = self._evaluate_context(context)

        reasoning = self._build_reasoning(decision_type, context)

        decision = {
            "decision_id": str(uuid.uuid4()),
            "decision_type": decision_type,
            "context_summary": {
                "queue_depth": context.get("queue_depth", 0),
                "active_workers": context.get("active_workers", 0),
                "cpu_utilization": context.get("cpu_utilization", 0),
                "memory_utilization": context.get("memory_utilization", 0),
                "error_rate": context.get("error_rate", 0),
            },
            "reasoning": reasoning,
            "action": self._build_action(decision_type, context),
            "confidence": self._calculate_confidence(decision_type, context),
            "created_at": datetime.utcnow().isoformat(),
        }

        async with self._lock:
            self._decisions.append(decision)
            if len(self._decisions) > self._max_decisions:
                self._decisions = self._decisions[-self._max_decisions :]

        if self._redis:
            try:
                await self._redis.rpush(
                    "orchestration:decisions", json.dumps(decision)
                )
                await self._redis.ltrim(
                    "orchestration:decisions", -self._max_decisions, -1
                )
            except Exception:
                pass

        return decision

    async def get_decisions(
        self, limit: int = 50, decision_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        decisions = list(self._decisions)
        if decision_type:
            decisions = [d for d in decisions if d.get("decision_type") == decision_type]
        return decisions[-limit:]

    async def evaluate_health(
        self,
        scheduler_stats: Dict[str, Any],
        resource_stats: Dict[str, Any],
    ) -> Dict[str, Any]:
        issues: List[Dict[str, Any]] = []
        score = 100.0

        queue_depth = scheduler_stats.get("queue_depths", {})
        total_queued = sum(queue_depth.values())
        if total_queued > 50:
            issues.append(
                {
                    "severity": "warning",
                    "component": "scheduler",
                    "message": f"High queue depth: {total_queued} tasks queued",
                }
            )
            score -= 15

        cpu_util = resource_stats.get("cpu_utilization_pct", 0)
        if cpu_util > 90:
            issues.append(
                {
                    "severity": "critical",
                    "component": "resources",
                    "message": f"CPU utilization critical: {cpu_util}%",
                }
            )
            score -= 30
        elif cpu_util > 75:
            issues.append(
                {
                    "severity": "warning",
                    "component": "resources",
                    "message": f"CPU utilization high: {cpu_util}%",
                }
            )
            score -= 10

        mem_util = resource_stats.get("memory_utilization_pct", 0)
        if mem_util > 90:
            issues.append(
                {
                    "severity": "critical",
                    "component": "resources",
                    "message": f"Memory utilization critical: {mem_util}%",
                }
            )
            score -= 25
        elif mem_util > 75:
            issues.append(
                {
                    "severity": "warning",
                    "component": "resources",
                    "message": f"Memory utilization high: {mem_util}%",
                }
            )
            score -= 10

        by_status = scheduler_stats.get("by_status", {})
        failed = by_status.get("failed", 0)
        total = scheduler_stats.get("total_tasks", 1)
        error_rate = failed / max(total, 1)
        if error_rate > 0.2:
            issues.append(
                {
                    "severity": "critical",
                    "component": "scheduler",
                    "message": f"High error rate: {error_rate:.1%}",
                }
            )
            score -= 20

        score = max(0, score)

        if score >= 90:
            status = "healthy"
        elif score >= 70:
            status = "degraded"
        elif score >= 40:
            status = "unhealthy"
        else:
            status = "critical"

        return {
            "status": status,
            "score": round(score, 1),
            "issues": issues,
            "checked_at": datetime.utcnow().isoformat(),
        }

    def _evaluate_context(self, context: Dict[str, Any]) -> str:
        queue_depth = context.get("queue_depth", 0)
        active_workers = context.get("active_workers", 0)
        cpu_util = context.get("cpu_utilization", 0)
        error_rate = context.get("error_rate", 0)

        if error_rate > 0.3:
            return "recover"
        if cpu_util > 90:
            return "throttle"
        if queue_depth > 20 and active_workers < 10:
            return "scale_up"
        if queue_depth == 0 and active_workers > 2:
            return "scale_down"
        if queue_depth > 0 and cpu_util < 50:
            return "reroute"
        return "defer"

    def _build_reasoning(
        self, decision_type: str, context: Dict[str, Any]
    ) -> str:
        templates = {
            "scale_up": (
                f"Queue depth is {context.get('queue_depth', 0)} with only "
                f"{context.get('active_workers', 0)} active workers. Scaling up "
                f"to reduce backlog."
            ),
            "scale_down": (
                f"Queue is empty with {context.get('active_workers', 0)} workers "
                f"active. Scaling down to save resources."
            ),
            "reroute": (
                f"Queue depth is {context.get('queue_depth', 0)} with CPU at "
                f"{context.get('cpu_utilization', 0)}%. Rerouting tasks to "
                f"underutilized nodes."
            ),
            "retry": (
                f"Error rate is {context.get('error_rate', 0):.1%}. Retrying "
                f"failed tasks with exponential backoff."
            ),
            "throttle": (
                f"CPU utilization at {context.get('cpu_utilization', 0)}% exceeds "
                f"safe threshold. Throttling new task admissions."
            ),
            "recover": (
                f"Error rate of {context.get('error_rate', 0):.1%} indicates "
                f"system instability. Initiating recovery procedures."
            ),
            "defer": (
                f"System metrics within acceptable ranges. Deferring action "
                f"until next evaluation cycle."
            ),
        }
        return templates.get(decision_type, "No specific reasoning available.")

    def _build_action(
        self, decision_type: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        if decision_type == "scale_up":
            target = min(context.get("active_workers", 0) + 2, 12)
            return {"type": "scale", "target_workers": target}
        elif decision_type == "scale_down":
            target = max(context.get("active_workers", 0) - 1, 2)
            return {"type": "scale", "target_workers": target}
        elif decision_type == "reroute":
            return {"type": "reroute", "strategy": "least_loaded"}
        elif decision_type == "retry":
            return {"type": "retry", "backoff_seconds": 5, "max_retries": 3}
        elif decision_type == "throttle":
            return {"type": "throttle", "max_new_tasks_per_minute": 5}
        elif decision_type == "recover":
            return {"type": "recover", "restart_failed_workers": True}
        return {"type": "none"}

    def _calculate_confidence(
        self, decision_type: str, context: Dict[str, Any]
    ) -> float:
        if decision_type == "defer":
            return 0.95
        queue_depth = context.get("queue_depth", 0)
        if queue_depth > 50 or context.get("error_rate", 0) > 0.3:
            return 0.9
        if queue_depth > 10:
            return 0.8
        return 0.7


# ============================================================
# Module-level singleton instances (lazy-initialized)
# ============================================================

_scheduler: Optional[ClusterScheduler] = None
_resource_manager: Optional[ResourceManager] = None
_decision_engine: Optional[AutonomousDecisionEngine] = None


def get_scheduler(redis_client=None) -> ClusterScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = ClusterScheduler(redis_client=redis_client)
    return _scheduler


def get_resource_manager(redis_client=None) -> ResourceManager:
    global _resource_manager
    if _resource_manager is None:
        _resource_manager = ResourceManager(redis_client=redis_client)
    return _resource_manager


def get_decision_engine(redis_client=None) -> AutonomousDecisionEngine:
    global _decision_engine
    if _decision_engine is None:
        _decision_engine = AutonomousDecisionEngine(redis_client=redis_client)
    return _decision_engine
