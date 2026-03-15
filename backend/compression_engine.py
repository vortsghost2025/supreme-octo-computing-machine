"""
Swarm Compression Engine - Idea Clustering and Blueprint Generation

Compresses and synthesizes ideas into:
- Concept clusters (grouped related ideas)
- Blueprint summaries (compressed knowledge)
- Knowledge graphs (linked concepts)
- Insights (compressed wisdom)
"""

import asyncio
import hashlib
import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum
import os

# Configuration
COMPRESSION_MIN_IDEAS = 5
COMPRESSION_MAX_IDEAS = 100
BLUEPRINT_MAX_TOKENS = 2000
CLUSTER_SIMILARITY_THRESHOLD = 0.6
INSIGHT_CONFIDENCE_THRESHOLD = 0.7

# Redis keys
_COMPRESSION_PREFIX = "compression"
_COMPRESSION_CLUSTER_PREFIX = "compression:cluster"
_COMPRESSION_BLUEPRINT_PREFIX = "compression:blueprint"
_COMPRESSION_INSIGHT_PREFIX = "compression:insight"
_COMPRESSION_GRAPH_PREFIX = "compression:graph"


class ClusterType(Enum):
    """Type of idea cluster."""

    THEMATIC = "thematic"  # Similar topics
    TEMPORAL = "temporal"  # Time-based grouping
    CAUSAL = "causal"  # Cause-effect relationships
    SEMANTIC = "semantic"  # Semantic similarity


@dataclass
class ConceptCluster:
    """A cluster of related ideas."""

    id: str
    name: str
    description: str
    cluster_type: ClusterType
    idea_ids: List[str] = field(default_factory=list)
    centroid: Optional[List[float]] = None
    keywords: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    compression_ratio: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "cluster_type": self.cluster_type.value,
            "idea_ids": self.idea_ids,
            "keywords": self.keywords,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "compression_ratio": self.compression_ratio,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConceptCluster":
        return cls(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            cluster_type=ClusterType(data.get("cluster_type", "thematic")),
            idea_ids=data.get("idea_ids", []),
            centroid=data.get("centroid"),
            keywords=data.get("keywords", []),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            compression_ratio=data.get("compression_ratio", 0.0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Blueprint:
    """A compressed summary of ideas."""

    id: str
    title: str
    content: str
    source_cluster_id: str
    key_points: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    relationships: List[Dict[str, str]] = field(default_factory=list)
    confidence: float = 0.0
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "source_cluster_id": self.source_cluster_id,
            "key_points": self.key_points,
            "entities": self.entities,
            "relationships": self.relationships,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Blueprint":
        return cls(
            id=data["id"],
            title=data["title"],
            content=data["content"],
            source_cluster_id=data["source_cluster_id"],
            key_points=data.get("key_points", []),
            entities=data.get("entities", []),
            relationships=data.get("relationships", []),
            confidence=data.get("confidence", 0.0),
            created_at=data.get("created_at", time.time()),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Insight:
    """A synthesized insight from compressed knowledge."""

    id: str
    content: str
    blueprint_ids: List[str] = field(default_factory=list)
    confidence: float = 0.0
    impact: str = "medium"  # low, medium, high
    category: str = "general"
    evidence: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "blueprint_ids": self.blueprint_ids,
            "confidence": self.confidence,
            "impact": self.impact,
            "category": self.category,
            "evidence": self.evidence,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Insight":
        return cls(
            id=data["id"],
            content=data["content"],
            blueprint_ids=data.get("blueprint_ids", []),
            confidence=data.get("confidence", 0.0),
            impact=data.get("impact", "medium"),
            category=data.get("category", "general"),
            evidence=data.get("evidence", []),
            created_at=data.get("created_at", time.time()),
            metadata=data.get("metadata", {}),
        )


@dataclass
class KnowledgeGraph:
    """A graph of linked concepts."""

    id: str
    name: str
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[Dict[str, Any]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "nodes": self.nodes,
            "edges": self.edges,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }


class SwarmCompressionEngine:
    """
    Engine for compressing ideas into clusters, blueprints, and insights.

    Pipeline:
    1. Cluster ideas by similarity
    2. Generate blueprint summaries
    3. Extract entities and relationships
    4. Synthesize insights
    """

    def __init__(
        self,
        redis_client,
        embedding_provider: Any = None,
        llm_provider: Any = None,
        node_id: str = None,
    ):
        self.redis = redis_client
        self.embedding_provider = embedding_provider  # For semantic clustering
        self.llm_provider = llm_provider  # For summarization
        self.node_id = (
            node_id
            or f"compression-{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"
        )

    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID."""
        return f"{prefix}-{int(time.time() * 1000)}"

    async def cluster_ideas(
        self,
        idea_ids: List[str],
        cluster_type: ClusterType = ClusterType.SEMANTIC,
        max_clusters: int = 10,
    ) -> List[ConceptCluster]:
        """Cluster ideas into related groups."""
        if len(idea_ids) < COMPRESSION_MIN_IDEAS:
            return []

        # Get ideas from Redis
        ideas = []
        for idea_id in idea_ids:
            data = await self.redis.get(f"idea:{idea_id}")
            if data:
                ideas.append(
                    json.loads(data.decode() if isinstance(data, bytes) else data)
                )

        if len(ideas) < COMPRESSION_MIN_IDEAS:
            return []

        # Simple clustering by keywords (placeholder for semantic clustering)
        keyword_clusters: Dict[str, List] = defaultdict(list)

        for idea in ideas:
            # Extract keywords from tags
            tags = idea.get("tags", [])
            content = idea.get("content", "")

            # Simple keyword extraction (first 3 words as proxy)
            words = content.lower().split()[:3]
            for word in words:
                if len(word) > 3:
                    keyword_clusters[word].append(idea.get("id"))
                    break

            # Also cluster by tags
            for tag in tags[:2]:
                keyword_clusters[tag].append(idea.get("id"))

        # Create clusters
        clusters = []
        used_ideas = set()

        for keyword, ids in sorted(
            keyword_clusters.items(), key=lambda x: len(x[1]), reverse=True
        ):
            # Skip if too few ideas or already used
            cluster_ids = [i for i in ids if i not in used_ideas]
            if len(cluster_ids) < COMPRESSION_MIN_IDEAS:
                continue

            # Limit cluster size
            cluster_ids = cluster_ids[:COMPRESSION_MAX_IDEAS]

            cluster = ConceptCluster(
                id=self._generate_id("cluster"),
                name=f"Cluster: {keyword}",
                description=f"Ideas related to {keyword}",
                cluster_type=cluster_type,
                idea_ids=cluster_ids,
                keywords=[keyword],
                compression_ratio=1
                - (len(cluster_ids) / (len(cluster_ids) * 10)),  # Placeholder
            )

            # Store cluster
            await self.redis.set(
                f"{_COMPRESSION_CLUSTER_PREFIX}:{cluster.id}",
                json.dumps(cluster.to_dict()),
            )

            clusters.append(cluster)
            used_ideas.update(cluster_ids)

            if len(clusters) >= max_clusters:
                break

        return clusters

    async def generate_blueprint(
        self,
        cluster_id: str,
    ) -> Optional[Blueprint]:
        """Generate a blueprint summary from a cluster."""
        # Get cluster
        data = await self.redis.get(f"{_COMPRESSION_CLUSTER_PREFIX}:{cluster_id}")
        if not data:
            return None

        cluster = ConceptCluster.from_dict(
            json.loads(data.decode() if isinstance(data, bytes) else data)
        )

        if len(cluster.idea_ids) < COMPRESSION_MIN_IDEAS:
            return None

        # Get ideas
        ideas = []
        for idea_id in cluster.idea_ids[:COMPRESSION_MAX_IDEAS]:
            idea_data = await self.redis.get(f"idea:{idea_id}")
            if idea_data:
                ideas.append(
                    json.loads(
                        idea_data.decode()
                        if isinstance(idea_data, bytes)
                        else idea_data
                    )
                )

        if not ideas:
            return None

        # Generate summary
        if self.llm_provider:
            # Use LLM to summarize
            try:
                content = "\n\n".join([f"- {i.get('content', '')}" for i in ideas])
                summary = await self.llm_provider.summarize(
                    content, max_tokens=BLUEPRINT_MAX_TOKENS
                )
            except Exception as e:
                print(f"LLM summarization error: {e}")
                summary = self._generate_simple_summary(ideas)
        else:
            summary = self._generate_simple_summary(ideas)

        # Extract entities and key points
        entities = self._extract_entities(ideas)
        key_points = self._extract_key_points(ideas)

        # Create blueprint
        blueprint = Blueprint(
            id=self._generate_id("blueprint"),
            title=cluster.name,
            content=summary,
            source_cluster_id=cluster_id,
            key_points=key_points,
            entities=entities,
            confidence=min(1.0, len(ideas) / 10),
        )

        # Store blueprint
        await self.redis.set(
            f"{_COMPRESSION_BLUEPRINT_PREFIX}:{blueprint.id}",
            json.dumps(blueprint.to_dict()),
        )

        return blueprint

    def _generate_simple_summary(self, ideas: List[Dict]) -> str:
        """Generate a simple summary without LLM."""
        if not ideas:
            return ""

        # Get top ideas by importance
        sorted_ideas = sorted(
            ideas, key=lambda x: x.get("importance", 0.5), reverse=True
        )

        # Take top 5
        top_ideas = sorted_ideas[:5]

        summary_parts = []
        for idea in top_ideas:
            content = idea.get("content", "")
            # Truncate
            if len(content) > 200:
                content = content[:200] + "..."
            summary_parts.append(content)

        return f"Summary of {len(ideas)} ideas:\n\n" + "\n\n".join(summary_parts)

    def _extract_entities(self, ideas: List[Dict]) -> List[str]:
        """Extract entities from ideas (placeholder)."""
        entities = set()

        for idea in ideas:
            content = idea.get("content", "")
            tags = idea.get("tags", [])

            # Use tags as entities
            entities.update(tags)

            # Simple extraction: capitalized words
            words = content.split()
            for word in words:
                if word and word[0].isupper() and len(word) > 2:
                    entities.add(word)

        return list(entities)[:50]  # Limit

    def _extract_key_points(self, ideas: List[Dict]) -> List[str]:
        """Extract key points from ideas."""
        key_points = []

        for idea in ideas[:10]:  # Limit to top 10
            content = idea.get("content", "")

            # Take first sentence or truncate
            if "." in content:
                first_sentence = content.split(".")[0]
                if len(first_sentence) > 20:
                    key_points.append(first_sentence + ".")
            else:
                key_points.append(content[:100] + "...")

        return key_points[:10]  # Limit to 10 key points

    async def synthesize_insight(
        self,
        blueprint_ids: List[str],
    ) -> Optional[Insight]:
        """Synthesize an insight from multiple blueprints."""
        if len(blueprint_ids) < 2:
            return None

        # Get blueprints
        blueprints = []
        for bp_id in blueprint_ids:
            data = await self.redis.get(f"{_COMPRESSION_BLUEPRINT_PREFIX}:{bp_id}")
            if data:
                blueprints.append(
                    Blueprint.from_dict(
                        json.loads(data.decode() if isinstance(data, bytes) else data)
                    )
                )

        if len(blueprints) < 2:
            return None

        # Synthesize content
        if self.llm_provider:
            try:
                content = "\n\n".join(
                    [f"## {bp.title}\n{bp.content}" for bp in blueprints]
                )
                insight_content = await self.llm_provider.synthesize(content)
            except Exception:
                insight_content = self._generate_simple_insight(blueprints)
        else:
            insight_content = self._generate_simple_insight(blueprints)

        # Calculate confidence based on number of sources
        confidence = min(1.0, len(blueprints) / 5)

        # Determine impact
        impact = "low"
        if confidence > 0.8:
            impact = "high"
        elif confidence > 0.5:
            impact = "medium"

        # Create insight
        insight = Insight(
            id=self._generate_id("insight"),
            content=insight_content,
            blueprint_ids=blueprint_ids,
            confidence=confidence,
            impact=impact,
            category=self._categorize_insight(blueprints),
            evidence=[bp.title for bp in blueprints],
        )

        # Store insight
        await self.redis.set(
            f"{_COMPRESSION_INSIGHT_PREFIX}:{insight.id}",
            json.dumps(insight.to_dict()),
        )

        return insight

    def _generate_simple_insight(self, blueprints: List[Blueprint]) -> str:
        """Generate simple insight without LLM."""
        if not blueprints:
            return ""

        # Find common entities
        all_entities = []
        for bp in blueprints:
            all_entities.extend(bp.entities)

        entity_counts = {}
        for entity in all_entities:
            entity_counts[entity] = entity_counts.get(entity, 0) + 1

        # Get most common
        common_entities = sorted(
            entity_counts.items(), key=lambda x: x[1], reverse=True
        )[:5]

        return f"Insight from {len(blueprints)} sources. Common themes: {', '.join([e[0] for e in common_entities])}"

    def _categorize_insight(self, blueprints: List[Blueprint]) -> str:
        """Categorize insight based on content."""
        categories = set()

        for bp in blueprints:
            title = bp.title.lower()
            if "code" in title or "build" in title:
                categories.add("technical")
            if "research" in title or "data" in title:
                categories.add("research")
            if "plan" in title or "strategy" in title:
                categories.add("strategy")

        if not categories:
            return "general"

        return list(categories)[0]

    async def run_compression_cycle(
        self,
        idea_ids: List[str],
    ) -> Dict[str, Any]:
        """Run full compression cycle: cluster -> blueprint -> insight."""
        results = {
            "clusters": [],
            "blueprints": [],
            "insights": [],
        }

        # Step 1: Cluster ideas
        clusters = await self.cluster_ideas(idea_ids)
        results["clusters"] = [c.to_dict() for c in clusters]

        # Step 2: Generate blueprints for each cluster
        for cluster in clusters:
            blueprint = await self.generate_blueprint(cluster.id)
            if blueprint:
                results["blueprints"].append(blueprint.to_dict())

        # Step 3: Synthesize insights from blueprints
        if len(results["blueprints"]) >= 2:
            insight = await self.synthesize_insight(
                [bp["id"] for bp in results["blueprints"]]
            )
            if insight:
                results["insights"].append(insight.to_dict())

        return results

    async def get_cluster(self, cluster_id: str) -> Optional[ConceptCluster]:
        """Get a cluster by ID."""
        data = await self.redis.get(f"{_COMPRESSION_CLUSTER_PREFIX}:{cluster_id}")
        if data:
            return ConceptCluster.from_dict(
                json.loads(data.decode() if isinstance(data, bytes) else data)
            )
        return None

    async def get_blueprint(self, blueprint_id: str) -> Optional[Blueprint]:
        """Get a blueprint by ID."""
        data = await self.redis.get(f"{_COMPRESSION_BLUEPRINT_PREFIX}:{blueprint_id}")
        if data:
            return Blueprint.from_dict(
                json.loads(data.decode() if isinstance(data, bytes) else data)
            )
        return None

    async def get_insight(self, insight_id: str) -> Optional[Insight]:
        """Get an insight by ID."""
        data = await self.redis.get(f"{_COMPRESSION_INSIGHT_PREFIX}:{insight_id}")
        if data:
            return Insight.from_dict(
                json.loads(data.decode() if isinstance(data, bytes) else data)
            )
        return None

    async def get_stats(self) -> Dict[str, Any]:
        """Get compression engine statistics."""
        cluster_keys = await self.redis.keys(f"{_COMPRESSION_CLUSTER_PREFIX}:*")
        blueprint_keys = await self.redis.keys(f"{_COMPRESSION_BLUEPRINT_PREFIX}:*")
        insight_keys = await self.redis.keys(f"{_COMPRESSION_INSIGHT_PREFIX}:*")

        return {
            "node_id": self.node_id,
            "total_clusters": len(cluster_keys),
            "total_blueprints": len(blueprint_keys),
            "total_insights": len(insight_keys),
        }


# Global instance
_compression_engine: Optional[SwarmCompressionEngine] = None


async def get_compression_engine() -> SwarmCompressionEngine:
    """Get the global Compression Engine instance."""
    global _compression_engine
    if _compression_engine is None:
        raise RuntimeError("Compression Engine not initialized")
    return _compression_engine


async def init_compression_engine(
    redis_client,
    embedding_provider: Any = None,
    llm_provider: Any = None,
    node_id: str = None,
) -> SwarmCompressionEngine:
    """Initialize the global Compression Engine."""
    global _compression_engine
    _compression_engine = SwarmCompressionEngine(
        redis_client, embedding_provider, llm_provider, node_id
    )
    return _compression_engine
