"""
Parallel Cognition Engine - Agent Forking and Result Merging

Enables parallel execution of agent tasks with:
- Agent forking (spawn multiple agents from one)
- Result merging with conflict resolution
- State synchronization across forks
- Speculative execution
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import os

# Configuration
MAX_FORKS = 16
FORK_TIMEOUT_SECONDS = 300
MERGE_STRATEGY_AUTO = "auto"
MERGE_STRATEGY_MAJORITY = "majority"
MERGE_STRATEGY_CONSENSUS = "consensus"
MERGE_STRATEGY_FIRST = "first"
MERGE_STRATEGY_LAST = "last"

# Redis keys
_PARALLEL_PREFIX = "parallel"
_PARALLEL_SESSION_PREFIX = "parallel:session"
_PARALLEL_FORK_PREFIX = "parallel:fork"
_PARALLEL_RESULT_PREFIX = "parallel:result"
_PARALLEL_MERGE_PREFIX = "parallel:merge"
_PARALLEL_STATE_PREFIX = "parallel:state"


class ForkStatus(Enum):
    """Status of a forked agent."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    MERGED = "merged"
    CANCELLED = "cancelled"


class MergeStrategy(Enum):
    """Strategy for merging fork results."""

    AUTO = "auto"
    MAJORITY = "majority"
    CONSENSUS = "consensus"
    FIRST = "first"
    LAST = "last"
    UNION = "union"
    INTERSECTION = "intersection"


@dataclass
class Fork:
    """Represents a forked agent."""

    id: str
    session_id: str
    parent_id: str
    task: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: ForkStatus = ForkStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    worker_id: Optional[str] = None
    priority: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "parent_id": self.parent_id,
            "task": self.task,
            "parameters": self.parameters,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "error": self.error,
            "worker_id": self.worker_id,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Fork":
        return cls(
            id=data["id"],
            session_id=data["session_id"],
            parent_id=data["parent_id"],
            task=data["task"],
            parameters=data.get("parameters", {}),
            status=ForkStatus(data.get("status", "pending")),
            created_at=data.get("created_at", time.time()),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            result=data.get("result"),
            error=data.get("error"),
            worker_id=data.get("worker_id"),
            priority=data.get("priority", 0),
        )


@dataclass
class ParallelSession:
    """Manages a parallel cognition session with multiple forks."""

    id: str
    original_task: str
    strategy: MergeStrategy = MergeStrategy.AUTO
    forks: List[str] = field(default_factory=list)
    merged_result: Optional[Dict[str, Any]] = None
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "original_task": self.original_task,
            "strategy": self.strategy.value,
            "forks": self.forks,
            "merged_result": self.merged_result,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParallelSession":
        return cls(
            id=data["id"],
            original_task=data["original_task"],
            strategy=MergeStrategy(data.get("strategy", "auto")),
            forks=data.get("forks", []),
            merged_result=data.get("merged_result"),
            created_at=data.get("created_at", time.time()),
            completed_at=data.get("completed_at"),
            metadata=data.get("metadata", {}),
        )


class ParallelCognitionEngine:
    """
    Engine for parallel agent execution with forking and merging.

    Features:
    - Spawn multiple agent forks from single task
    - Execute forks in parallel
    - Merge results with configurable strategies
    - Handle conflicts and edge cases
    - State synchronization across forks
    """

    def __init__(
        self,
        redis_client,
        executor: Callable = None,
        node_id: str = None,
    ):
        self.redis = redis_client
        self.executor = executor  # Function to execute a fork
        self.node_id = (
            node_id
            or f"parallel-{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"
        )

        # In-memory tracking
        self._active_sessions: Dict[str, ParallelSession] = {}
        self._active_forks: Dict[str, Fork] = {}
        self._fork_results: Dict[str, Any] = {}

    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID."""
        return f"{prefix}-{self.node_id}-{int(time.time() * 1000)}"

    async def create_session(
        self,
        task: str,
        num_forks: int = None,
        strategy: MergeStrategy = MergeStrategy.AUTO,
        parameters: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """
        Create a parallel cognition session.

        Returns session ID.
        """
        # Determine number of forks
        if num_forks is None:
            num_forks = parameters.get("num_forks", 3) if parameters else 3
        num_forks = min(num_forks, MAX_FORKS)

        # Create session
        session_id = self._generate_id("session")
        session = ParallelSession(
            id=session_id,
            original_task=task,
            strategy=strategy,
            metadata=metadata or {},
        )

        # Store session
        await self.redis.set(
            f"{_PARALLEL_SESSION_PREFIX}:{session_id}",
            json.dumps(session.to_dict()),
        )

        # Create forks
        for i in range(num_forks):
            fork_id = self._generate_id("fork")

            # Vary parameters for each fork
            fork_params = (parameters or {}).copy()
            fork_params["_fork_index"] = i
            fork_params["_fork_total"] = num_forks

            fork = Fork(
                id=fork_id,
                session_id=session_id,
                parent_id=session_id,
                task=task,
                parameters=fork_params,
                priority=-i,  # Higher priority for earlier forks
            )

            # Store fork
            await self.redis.set(
                f"{_PARALLEL_FORK_PREFIX}:{fork_id}",
                json.dumps(fork.to_dict()),
            )

            session.forks.append(fork_id)
            self._active_forks[fork_id] = fork

        # Update session with forks
        await self.redis.set(
            f"{_PARALLEL_SESSION_PREFIX}:{session_id}",
            json.dumps(session.to_dict()),
        )

        self._active_sessions[session_id] = session
        return session_id

    async def execute_session(
        self,
        session_id: str,
        timeout: int = FORK_TIMEOUT_SECONDS,
    ) -> Dict[str, Any]:
        """
        Execute all forks in a session in parallel.

        Returns merged result.
        """
        # Get session
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # Execute forks in parallel
        tasks = []
        for fork_id in session.forks:
            task = asyncio.create_task(self._execute_fork(fork_id, timeout))
            tasks.append(task)

        # Wait for all forks
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Store results
        for fork_id, result in zip(session.forks, results):
            if isinstance(result, Exception):
                await self._set_fork_error(fork_id, str(result))
            else:
                self._fork_results[fork_id] = result

        # Merge results
        merged = await self._merge_results(session)

        # Update session
        session.merged_result = merged
        session.completed_at = time.time()
        await self.redis.set(
            f"{_PARALLEL_SESSION_PREFIX}:{session_id}",
            json.dumps(session.to_dict()),
        )

        return merged

    async def _execute_fork(self, fork_id: str, timeout: int) -> Dict[str, Any]:
        """Execute a single fork."""
        # Get fork
        fork = await self.get_fork(fork_id)
        if not fork:
            raise ValueError(f"Fork {fork_id} not found")

        # Update status to running
        fork.status = ForkStatus.RUNNING
        fork.started_at = time.time()
        await self.redis.set(
            f"{_PARALLEL_FORK_PREFIX}:{fork_id}",
            json.dumps(fork.to_dict()),
        )

        # Execute using provided executor or default
        if self.executor:
            result = await asyncio.wait_for(
                self.executor(fork.task, fork.parameters),
                timeout=timeout,
            )
        else:
            # Default: simulate execution
            await asyncio.sleep(0.1)
            result = {
                "fork_id": fork_id,
                "task": fork.task,
                "output": f"Executed fork {fork_id}",
                "parameters": fork.parameters,
            }

        # Update status to completed
        fork.status = ForkStatus.COMPLETED
        fork.completed_at = time.time()
        fork.result = result
        await self.redis.set(
            f"{_PARALLEL_FORK_PREFIX}:fork_id",
            json.dumps(fork.to_dict()),
        )

        return result

    async def _set_fork_error(self, fork_id: str, error: str):
        """Mark fork as failed with error."""
        fork = await self.get_fork(fork_id)
        if fork:
            fork.status = ForkStatus.FAILED
            fork.completed_at = time.time()
            fork.error = error
            await self.redis.set(
                f"{_PARALLEL_FORK_PREFIX}:{fork_id}",
                json.dumps(fork.to_dict()),
            )

    async def _merge_results(self, session: ParallelSession) -> Dict[str, Any]:
        """Merge results from all forks based on strategy."""
        results = []
        for fork_id in session.forks:
            fork = await self.get_fork(fork_id)
            if fork and fork.status == ForkStatus.COMPLETED and fork.result:
                results.append(fork.result)

        if not results:
            return {
                "error": "No successful results to merge",
                "strategy": session.strategy.value,
            }

        # Apply merge strategy
        if session.strategy == MergeStrategy.FIRST:
            return results[0]

        elif session.strategy == MergeStrategy.LAST:
            return results[-1]

        elif session.strategy == MergeStrategy.MAJORITY:
            return self._merge_majority(results)

        elif session.strategy == MergeStrategy.CONSENSUS:
            return self._merge_consensus(results)

        elif session.strategy == MergeStrategy.UNION:
            return self._merge_union(results)

        elif session.strategy == MergeStrategy.INTERSECTION:
            return self._merge_intersection(results)

        else:  # AUTO
            # Choose strategy based on results
            return self._merge_auto(results)

    def _merge_majority(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge by selecting most common values."""
        if len(results) == 1:
            return results[0]

        # Find most common values for each key
        merged = {}
        keys = set()
        for r in results:
            keys.update(r.keys())

        for key in keys:
            values = [r.get(key) for r in results if key in r]
            if values:
                # Count occurrences
                counts = {}
                for v in values:
                    v_str = json.dumps(v, sort_keys=True)
                    counts[v_str] = counts.get(v_str, 0) + 1

                # Get most common
                most_common = max(counts.items(), key=lambda x: x[1])
                merged[key] = json.loads(most_common[0])

        merged["_merge_strategy"] = "majority"
        return merged

    def _merge_consensus(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge by finding consensus (unanimous or near-unanimous)."""
        if len(results) == 1:
            return results[0]

        merged = {}
        keys = set()
        for r in results:
            keys.update(r.keys())

        threshold = len(results) * 0.7  # 70% consensus

        for key in keys:
            values = [r.get(key) for r in results if key in r]
            if values:
                # Count occurrences
                counts = {}
                for v in values:
                    v_str = json.dumps(v, sort_keys=True)
                    counts[v_str] = counts.get(v_str, 0) + 1

                # Get consensus value if threshold met
                max_count = max(counts.values())
                if max_count >= threshold:
                    consensus = max(counts.items(), key=lambda x: x[1])
                    merged[key] = json.loads(consensus[0])
                else:
                    # Keep all values as list
                    merged[key] = values

        merged["_merge_strategy"] = "consensus"
        return merged

    def _merge_union(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge by taking union of all values."""
        merged = {}

        for r in results:
            for key, value in r.items():
                if key not in merged:
                    if isinstance(value, list):
                        merged[key] = []
                    else:
                        merged[key] = value

                # Add to list if not present
                if isinstance(merged[key], list) and isinstance(value, list):
                    for v in value:
                        if v not in merged[key]:
                            merged[key].append(v)

        merged["_merge_strategy"] = "union"
        return merged

    def _merge_intersection(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge by taking intersection of all values."""
        if not results:
            return {}

        merged = {}
        keys = set(results[0].keys())
        for r in results[1:]:
            keys &= r.keys()

        for key in keys:
            values = [r.get(key) for r in results]
            if all(v == values[0] for v in values):
                merged[key] = values[0]

        merged["_merge_strategy"] = "intersection"
        return merged

    def _merge_auto(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Auto-select merge strategy based on result similarity."""
        if len(results) == 1:
            return results[0]

        # Check similarity
        keys_sets = [set(r.keys()) for r in results]
        common_keys = keys_sets[0]
        for ks in keys_sets[1:]:
            common_keys &= ks

        # If very similar, use majority
        if len(common_keys) >= len(results[0]) * 0.7:
            return self._merge_majority(results)

        # Otherwise use union
        return self._merge_union(results)

    async def get_session(self, session_id: str) -> Optional[ParallelSession]:
        """Get a parallel session."""
        data = await self.redis.get(f"{_PARALLEL_SESSION_PREFIX}:{session_id}")
        if data:
            return ParallelSession.from_dict(
                json.loads(data.decode() if isinstance(data, bytes) else data)
            )
        return None

    async def get_fork(self, fork_id: str) -> Optional[Fork]:
        """Get a fork."""
        data = await self.redis.get(f"{_PARALLEL_FORK_PREFIX}:{fork_id}")
        if data:
            return Fork.from_dict(
                json.loads(data.decode() if isinstance(data, bytes) else data)
            )
        return None

    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get status of all forks in a session."""
        session = await self.get_session(session_id)
        if not session:
            return {"error": "Session not found"}

        fork_statuses = []
        for fork_id in session.forks:
            fork = await self.get_fork(fork_id)
            if fork:
                fork_statuses.append(
                    {
                        "id": fork.id,
                        "status": fork.status.value,
                        "result": fork.result is not None,
                        "error": fork.error,
                    }
                )

        return {
            "session_id": session_id,
            "strategy": session.strategy.value,
            "forks": fork_statuses,
            "completed": session.completed_at is not None,
            "merged_result": session.merged_result,
        }

    async def cancel_session(self, session_id: str) -> int:
        """Cancel all forks in a session. Returns number of cancelled forks."""
        session = await self.get_session(session_id)
        if not session:
            return 0

        cancelled = 0
        for fork_id in session.forks:
            fork = await self.get_fork(fork_id)
            if fork and fork.status in [ForkStatus.PENDING, ForkStatus.RUNNING]:
                fork.status = ForkStatus.CANCELLED
                fork.completed_at = time.time()
                await self.redis.set(
                    f"{_PARALLEL_FORK_PREFIX}:{fork_id}",
                    json.dumps(fork.to_dict()),
                )
                cancelled += 1

        return cancelled

    async def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        # Count keys
        session_keys = await self.redis.keys(f"{_PARALLEL_SESSION_PREFIX}:*")
        fork_keys = await self.redis.keys(f"{_PARALLEL_FORK_PREFIX}:*")

        return {
            "node_id": self.node_id,
            "total_sessions": len(session_keys),
            "total_forks": len(fork_keys),
            "active_sessions": len(self._active_sessions),
            "active_forks": len(self._active_forks),
        }


# Global instance
_parallel_engine: Optional[ParallelCognitionEngine] = None


async def get_parallel_engine() -> ParallelCognitionEngine:
    """Get the global Parallel Cognition Engine instance."""
    global _parallel_engine
    if _parallel_engine is None:
        raise RuntimeError("Parallel Cognition Engine not initialized")
    return _parallel_engine


async def init_parallel_engine(
    redis_client,
    executor: Callable = None,
    node_id: str = None,
) -> ParallelCognitionEngine:
    """Initialize the global Parallel Cognition Engine."""
    global _parallel_engine
    _parallel_engine = ParallelCognitionEngine(redis_client, executor, node_id)
    return _parallel_engine
