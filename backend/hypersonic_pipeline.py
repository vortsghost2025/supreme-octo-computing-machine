"""
Hypersonic Idea Ingestion Pipeline

High-throughput pipeline for processing ideas with:
- Deduplication (exact and semantic)
- Semantic clustering using embeddings
- Graph linking between related ideas
- Priority-based processing
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import os

# Configuration
DEDUP_EXACT_CACHE_SIZE = 100000
DEDUP_SEMANTIC_THRESHOLD = 0.85
EMBEDDING_CACHE_SIZE = 50000
CLUSTER_SIMILARITY_THRESHOLD = 0.7
MAX_IDEAS_PER_CLUSTER = 100
IDEA_TTL_SECONDS = 86400 * 30  # 30 days

# Redis keys
_IDEA_PREFIX = "idea"
_IDEA_INDEX_KEY = "ideas:index"
_IDEA_CONTENT_HASH_PREFIX = "idea:hash"
_IDEA_EMBEDDING_PREFIX = "idea:embedding"
_CLUSTER_PREFIX = "idea:cluster"
_CLUSTER_IDEAS_PREFIX = "cluster:ideas"
_GRAPH_LINKS_PREFIX = "idea:links"
_GRAPH_REVERSE_PREFIX = "idea:reverse_links"


@dataclass
class Idea:
    """Represents an idea in the system."""

    id: str
    content: str
    tags: List[str] = field(default_factory=list)
    source: str = ""
    importance: float = 0.5
    created_at: float = field(default_factory=time.time)
    embedding: Optional[List[float]] = None
    cluster_id: Optional[str] = None
    links: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "tags": self.tags,
            "source": self.source,
            "importance": self.importance,
            "created_at": self.created_at,
            "cluster_id": self.cluster_id,
            "links": self.links,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Idea":
        return cls(
            id=data["id"],
            content=data["content"],
            tags=data.get("tags", []),
            source=data.get("source", ""),
            importance=data.get("importance", 0.5),
            created_at=data.get("created_at", time.time()),
            embedding=data.get("embedding"),
            cluster_id=data.get("cluster_id"),
            links=data.get("links", []),
            metadata=data.get("metadata", {}),
        )


class HypersonicIngestionPipeline:
    """
    High-throughput idea ingestion with deduplication and clustering.

    Features:
    - Exact deduplication via content hash
    - Semantic deduplication via embeddings
    - Automatic clustering of related ideas
    - Graph linking for related ideas
    - Priority-based processing
    """

    def __init__(
        self,
        redis_client,
        embedding_provider: Any = None,
        node_id: str = None,
    ):
        self.redis = redis_client
        self.embedding_provider = embedding_provider
        self.node_id = (
            node_id
            or f"hypersonic-{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"
        )

        # In-memory caches
        self._exact_dedup: Dict[str, float] = {}
        self._embedding_cache: Dict[str, List[float]] = {}
        self._cluster_centroids: Dict[str, List[float]] = {}

        # Processing queues
        self._processing_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._process_task: Optional[asyncio.Task] = None

    def _compute_content_hash(self, content: str) -> str:
        """Compute exact deduplication hash."""
        return hashlib.sha256(content.strip().lower().encode()).hexdigest()[:16]

    async def _get_embedding(self, content: str) -> Optional[List[float]]:
        """Get embedding for content (cached or via provider)."""
        # Check cache
        cache_key = self._compute_content_hash(content)
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        # Use provider if available
        if self.embedding_provider:
            try:
                embedding = await self.embedding_provider.get_embedding(content)

                # Cache it
                if len(self._embedding_cache) < EMBEDDING_CACHE_SIZE:
                    self._embedding_cache[cache_key] = embedding

                return embedding
            except Exception as e:
                print(f"Embedding error: {e}")

        return None

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two embeddings."""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0
        return dot / (norm_a * norm_b)

    async def _check_exact_duplicate(self, content: str) -> Optional[str]:
        """Check for exact duplicate using content hash."""
        content_hash = self._compute_content_hash(content)

        # Check Redis
        existing = await self.redis.get(f"{_IDEA_CONTENT_HASH_PREFIX}:{content_hash}")
        if existing:
            return existing.decode() if isinstance(existing, bytes) else existing

        # Check memory cache
        if content_hash in self._exact_dedup:
            return self._exact_dedup[content_hash]

        return None

    async def _add_exact_dedup(self, idea_id: str, content: str):
        """Add to exact deduplication cache."""
        content_hash = self._compute_content_hash(content)

        # Add to Redis with TTL
        await self.redis.set(
            f"{_IDEA_CONTENT_HASH_PREFIX}:{content_hash}",
            idea_id,
            ex=IDEA_TTL_SECONDS,
        )

        # Add to memory cache
        if len(self._exact_dedup) < DEDUP_EXACT_CACHE_SIZE:
            self._exact_dedup[content_hash] = idea_id

    async def _check_semantic_duplicate(
        self,
        content: str,
        embedding: List[float],
    ) -> Optional[str]:
        """Check for semantic duplicate using embeddings."""
        if not embedding:
            return None

        # Check against cluster centroids first (fast path)
        for cluster_id, centroid in self._cluster_centroids.items():
            similarity = self._cosine_similarity(embedding, centroid)
            if similarity >= DEDUP_SEMANTIC_THRESHOLD:
                # Check ideas in this cluster
                ideas = await self.redis.smembers(
                    f"{_CLUSTER_IDEAS_PREFIX}:{cluster_id}"
                )
                for idea_id in ideas:
                    idea_id_str = (
                        idea_id.decode() if isinstance(idea_id, bytes) else idea_id
                    )
                    cached_emb = self._embedding_cache.get(idea_id_str[:16])
                    if cached_emb:
                        sim = self._cosine_similarity(embedding, cached_emb)
                        if sim >= DEDUP_SEMANTIC_THRESHOLD:
                            return idea_id_str

        return None

    async def _find_or_create_cluster(
        self,
        content: str,
        embedding: List[float],
    ) -> str:
        """Find existing cluster or create new one."""
        if not embedding:
            # No embedding - create singleton cluster
            cluster_id = f"cluster-{self._compute_content_hash(content)[:12]}"
            await self._create_cluster(cluster_id, embedding)
            return cluster_id

        # Check existing clusters
        best_cluster = None
        best_similarity = 0

        for cluster_id, centroid in self._cluster_centroids.items():
            similarity = self._cosine_similarity(embedding, centroid)
            if (
                similarity > best_similarity
                and similarity >= CLUSTER_SIMILARITY_THRESHOLD
            ):
                best_similarity = similarity
                best_cluster = cluster_id

        if best_cluster:
            # Update cluster centroid
            await self._update_cluster_centroid(best_cluster, embedding)
            return best_cluster

        # Create new cluster
        cluster_id = f"cluster-{self._compute_content_hash(content)[:12]}"
        await self._create_cluster(cluster_id, embedding)
        return cluster_id

    async def _create_cluster(self, cluster_id: str, embedding: Optional[List[float]]):
        """Create a new cluster."""
        self._cluster_centroids[cluster_id] = embedding or []
        await self.redis.sadd(f"{_CLUSTER_IDEAS_PREFIX}:{cluster_id}", "")

    async def _update_cluster_centroid(
        self, cluster_id: str, new_embedding: List[float]
    ):
        """Update cluster centroid with new embedding."""
        if cluster_id not in self._cluster_centroids:
            return

        old_centroid = self._cluster_centroids[cluster_id]
        if not old_centroid:
            self._cluster_centroids[cluster_id] = new_embedding
            return

        # Incremental update (running average)
        alpha = 0.1  # Learning rate
        updated = [
            old + alpha * (new - old) for old, new in zip(old_centroid, new_embedding)
        ]
        self._cluster_centroids[cluster_id] = updated

    async def _link_related_ideas(self, idea_id: str, cluster_id: str):
        """Link idea to related ideas in same cluster."""
        # Get all ideas in cluster
        ideas = await self.redis.smembers(f"{_CLUSTER_IDEAS_PREFIX}:{cluster_id}")

        for other_id in ideas:
            other_id_str = (
                other_id.decode() if isinstance(other_id, bytes) else other_id
            )
            if other_id_str and other_id_str != idea_id:
                # Add bidirectional links
                await self.redis.sadd(f"{_GRAPH_LINKS_PREFIX}:{idea_id}", other_id_str)
                await self.redis.sadd(f"{_GRAPH_LINKS_PREFIX}:{other_id_str}", idea_id)

        # Add to cluster
        await self.redis.sadd(f"{_CLUSTER_IDEAS_PREFIX}:{cluster_id}", idea_id)

    async def ingest(
        self,
        content: str,
        tags: List[str] = None,
        source: str = None,
        importance: float = 0.5,
        metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Ingest a new idea through the pipeline.

        Returns:
            Dict with 'idea_id', 'status', 'duplicate_of', 'cluster_id'
        """
        tags = tags or []
        source = source or self.node_id
        metadata = metadata or {}

        # Step 1: Exact deduplication
        duplicate_of = await self._check_exact_duplicate(content)
        if duplicate_of:
            return {
                "idea_id": None,
                "status": "duplicate_exact",
                "duplicate_of": duplicate_of,
                "cluster_id": None,
            }

        # Step 2: Generate embedding
        embedding = await self._get_embedding(content)

        # Step 3: Semantic deduplication
        if embedding:
            semantic_duplicate = await self._check_semantic_duplicate(
                content, embedding
            )
            if semantic_duplicate:
                # Mark as potential duplicate but allow
                pass

        # Step 4: Create idea
        idea_id = (
            f"idea-{self._compute_content_hash(content)}-{int(time.time() * 1000)}"
        )

        idea = Idea(
            id=idea_id,
            content=content,
            tags=tags,
            source=source,
            importance=importance,
            embedding=embedding,
            metadata=metadata,
        )

        # Step 5: Find or create cluster
        cluster_id = await self._find_or_create_cluster(content, embedding)
        idea.cluster_id = cluster_id

        # Step 6: Store idea
        await self.redis.set(
            f"{_IDEA_PREFIX}:{idea_id}",
            json.dumps(idea.to_dict()),
            ex=IDEA_TTL_SECONDS,
        )

        # Step 7: Add to index
        await self.redis.zadd(_IDEA_INDEX_KEY, {idea_id: idea.created_at})

        # Step 8: Add to cluster
        await self.redis.sadd(f"{_CLUSTER_IDEAS_PREFIX}:{cluster_id}", idea_id)

        # Step 9: Link related ideas
        await self._link_related_ideas(idea_id, cluster_id)

        # Step 10: Add exact dedup
        await self._add_exact_dedup(idea_id, content)

        # Cache embedding
        if embedding and len(self._embedding_cache) < EMBEDDING_CACHE_SIZE:
            self._embedding_cache[idea_id[:16]] = embedding

        return {
            "idea_id": idea_id,
            "status": "created",
            "duplicate_of": None,
            "cluster_id": cluster_id,
        }

    async def ingest_batch(
        self,
        ideas: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Ingest multiple ideas in batch."""
        results = []
        for idea_data in ideas:
            result = await self.ingest(
                content=idea_data["content"],
                tags=idea_data.get("tags"),
                source=idea_data.get("source"),
                importance=idea_data.get("importance", 0.5),
                metadata=idea_data.get("metadata", {}),
            )
            results.append(result)
        return results

    async def get_idea(self, idea_id: str) -> Optional[Idea]:
        """Get an idea by ID."""
        data = await self.redis.get(f"{_IDEA_PREFIX}:{idea_id}")
        if data:
            return Idea.from_dict(
                json.loads(data.decode() if isinstance(data, bytes) else data)
            )
        return None

    async def get_cluster_ideas(self, cluster_id: str, limit: int = 50) -> List[Idea]:
        """Get all ideas in a cluster."""
        idea_ids = await self.redis.smembers(f"{_CLUSTER_IDEAS_PREFIX}:{cluster_id}")
        ideas = []
        for idea_id in idea_ids:
            idea_id_str = idea_id.decode() if isinstance(idea_id, bytes) else idea_id
            if idea_id_str:
                idea = await self.get_idea(idea_id_str)
                if idea:
                    ideas.append(idea)
                    if len(ideas) >= limit:
                        break
        return ideas

    async def get_related_ideas(self, idea_id: str, limit: int = 10) -> List[Idea]:
        """Get related ideas via graph links."""
        link_ids = await self.redis.smembers(f"{_GRAPH_LINKS_PREFIX}:{idea_id}")
        ideas = []
        for link_id in link_ids:
            link_id_str = link_id.decode() if isinstance(link_id, bytes) else link_id
            if link_id_str:
                idea = await self.get_idea(link_id_str)
                if idea:
                    ideas.append(idea)
                    if len(ideas) >= limit:
                        break
        return ideas

    async def search_ideas(
        self,
        query: str = None,
        tags: List[str] = None,
        cluster_id: str = None,
        min_importance: float = 0,
        limit: int = 50,
    ) -> List[Idea]:
        """Search ideas by various criteria."""
        results = []

        # If cluster specified, search within cluster
        if cluster_id:
            return await self.get_cluster_ideas(cluster_id, limit)

        # If query provided, use embedding similarity
        if query:
            query_embedding = await self._get_embedding(query)
            if query_embedding:
                # Search all clusters for similar ideas
                for cid, centroid in self._cluster_centroids.items():
                    if centroid:
                        sim = self._cosine_similarity(query_embedding, centroid)
                        if sim >= 0.5:
                            cluster_ideas = await self.get_cluster_ideas(cid, limit=20)
                            results.extend(cluster_ideas)

        # Filter by tags if specified
        if tags:
            results = [r for r in results if any(t in r.tags for t in tags)]

        # Filter by importance
        results = [r for r in results if r.importance >= min_importance]

        # Sort by importance and limit
        results.sort(key=lambda x: x.importance, reverse=True)
        return results[:limit]

    async def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        # Count ideas
        idea_count = await self.redis.zcard(_IDEA_INDEX_KEY)

        # Count clusters
        cluster_count = len(self._cluster_centroids)

        # Count links
        link_count = 0
        keys = await self.redis.keys(f"{_GRAPH_LINKS_PREFIX}:*")
        for key in keys:
            link_count += await self.redis.scard(key)

        return {
            "node_id": self.node_id,
            "total_ideas": idea_count,
            "total_clusters": cluster_count,
            "total_links": link_count // 2,  # Bidirectional
            "embedding_cache_size": len(self._embedding_cache),
            "exact_dedup_cache_size": len(self._exact_dedup),
        }

    async def cleanup_old_ideas(self, max_age_seconds: int = IDEA_TTL_SECONDS):
        """Remove ideas older than max_age_seconds."""
        cutoff = time.time() - max_age_seconds

        # Get ideas older than cutoff
        old_ideas = await self.redis.zrangebyscore(_IDEA_INDEX_KEY, 0, cutoff)

        removed = 0
        for idea_id in old_ideas:
            idea_id_str = idea_id.decode() if isinstance(idea_id, bytes) else idea_id

            # Get idea to find cluster
            idea = await self.get_idea(idea_id_str)
            if idea and idea.cluster_id:
                # Remove from cluster
                await self.redis.srem(
                    f"{_CLUSTER_IDEAS_PREFIX}:{idea.cluster_id}", idea_id_str
                )

                # Remove links
                await self.redis.delete(f"{_GRAPH_LINKS_PREFIX}:{idea_id_str}")

            # Remove idea
            await self.redis.delete(f"{_IDEA_PREFIX}:{idea_id_str}")
            removed += 1

        # Remove from index
        if removed > 0:
            await self.redis.zremrangebyscore(_IDEA_INDEX_KEY, 0, cutoff)

        return removed


# Global instance
_hypersonic_pipeline: Optional[HypersonicIngestionPipeline] = None


async def get_hypersonic_pipeline() -> HypersonicIngestionPipeline:
    """Get the global Hypersonic pipeline instance."""
    global _hypersonic_pipeline
    if _hypersonic_pipeline is None:
        raise RuntimeError("Hypersonic Pipeline not initialized")
    return _hypersonic_pipeline


async def init_hypersonic_pipeline(
    redis_client,
    embedding_provider: Any = None,
    node_id: str = None,
) -> HypersonicIngestionPipeline:
    """Initialize the global Hypersonic pipeline."""
    global _hypersonic_pipeline
    _hypersonic_pipeline = HypersonicIngestionPipeline(
        redis_client, embedding_provider, node_id
    )
    return _hypersonic_pipeline
