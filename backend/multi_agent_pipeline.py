"""
Multi-Agent Pipeline - run multiple agents with different models in parallel
"""
import asyncio
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import httpx

# Import our router
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.model_router import router
from backend.llm_client import generate as ollama_generate, OLLAMA_BASE_URL


@dataclass
class AgentTask:
    """Single agent task"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    prompt: str = ""
    agent_type: str = "general"  # research, analysis, creative, review, coding
    model: Optional[str] = None  # None = auto-route
    context: Optional[str] = None
    timeout: int = 60


@dataclass
class AgentResult:
    """Agent execution result"""
    task_id: str
    agent_type: str
    model: str
    response: str
    success: bool
    duration: float
    error: Optional[str] = None


class MultiAgentPipeline:
    """Execute multiple agents in parallel with different models"""
    
    # Agent type to model preferences
    AGENT_CONFIGS = {
        "research": {"quality": "llama3:8b", "fast": "orca-mini:latest"},
        "analysis": {"balanced": "mistral:7b", "quality": "llama3:8b"},
        "creative": {"balanced": "mistral:7b", "fast": "orca-mini:latest"},
        "review": {"quality": "llama3:8b", "balanced": "mistral:7b"},
        "coding": {"quality": "llama3:8b", "balanced": "mistral:7b"},
        "general": {"balanced": "mistral:7b", "fast": "orca-mini:latest"},
    }
    
    def __init__(self, max_parallel: int = 4):
        self.max_parallel = max_parallel
        self.semaphore = asyncio.Semaphore(max_parallel)
    
    async def _run_single_agent(self, task: AgentTask) -> AgentResult:
        """Run a single agent with timeout"""
        async with self.semaphore:
            start = datetime.now()
            
            # Auto-route if no model specified
            if not task.model:
                route = router.route(task.prompt)
                task.model = route["model"]
            
            # Build the prompt with agent context
            full_prompt = task.prompt
            if task.context:
                full_prompt = f"{task.context}\n\nTask: {task.prompt}"
            
            # Add agent-specific system prompt
            system = self._get_agent_system(task.agent_type)
            
            try:
                result = await asyncio.wait_for(
                    ollama_generate(
                        prompt=full_prompt,
                        model=task.model,
                        system=system
                    ),
                    timeout=task.timeout
                )
                duration = (datetime.now() - start).total_seconds()
                
                return AgentResult(
                    task_id=task.task_id,
                    agent_type=task.agent_type,
                    model=task.model,
                    response=result,
                    success=True,
                    duration=duration
                )
            except asyncio.TimeoutError:
                duration = (datetime.now() - start).total_seconds()
                return AgentResult(
                    task_id=task.task_id,
                    agent_type=task.agent_type,
                    model=task.model or "unknown",
                    response="",
                    success=False,
                    duration=duration,
                    error=f"Timeout after {task.timeout}s"
                )
            except Exception as e:
                duration = (datetime.now() - start).total_seconds()
                return AgentResult(
                    task_id=task.task_id,
                    agent_type=task.agent_type,
                    model=task.model or "unknown",
                    response="",
                    success=False,
                    duration=duration,
                    error=str(e)
                )
    
    def _get_agent_system(self, agent_type: str) -> str:
        """Get system prompt for agent type"""
        systems = {
            "research": "You are a research assistant. Find facts, gather information, and cite sources.",
            "analysis": "You are an analysis expert. Break down problems, identify patterns, and provide insights.",
            "creative": "You are a creative writer. Be imaginative, descriptive, and engaging.",
            "review": "You are a code reviewer. Be thorough, constructive, and look for bugs and improvements.",
            "coding": "You are a coding assistant. Write clean, efficient, well-documented code.",
            "general": "You are a helpful AI assistant. Be clear and concise."
        }
        return systems.get(agent_type, systems["general"])
    
    async def run_parallel(self, tasks: List[AgentTask]) -> List[AgentResult]:
        """Run multiple agents in parallel"""
        results = await asyncio.gather(
            *[self._run_single_agent(task) for task in tasks],
            return_exceptions=True
        )
        
        # Handle any exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(AgentResult(
                    task_id=tasks[i].task_id,
                    agent_type=tasks[i].agent_type,
                    model=tasks[i].model or "unknown",
                    response="",
                    success=False,
                    duration=0,
                    error=str(result)
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def run_sequential(self, tasks: List[AgentTask]) -> List[AgentResult]:
        """Run agents sequentially (for dependent tasks)"""
        results = []
        for task in tasks:
            result = await self._run_single_agent(task)
            results.append(result)
            # Early exit on failure
            if not result.success:
                break
        return results
    
    async def run_delegate(self, prompt: str) -> Dict[str, AgentResult]:
        """
        Auto-delegate: break down prompt and run multiple specialized agents
        Returns dict of agent_type -> result
        """
        # Analyze prompt and create subtasks
        subtasks = self._create_subtasks(prompt)
        
        # Run all in parallel
        results = await self.run_parallel(subtasks)
        
        # Return as dict
        return {r.agent_type: r for r in results}
    
    def _create_subtasks(self, prompt: str) -> List[AgentTask]:
        """Break down a complex prompt into agent subtasks"""
        # Simple heuristic - in production, use LLM to decompose
        prompt_lower = prompt.lower()
        
        subtasks = []
        
        # Check if it needs research
        if any(k in prompt_lower for k in ["research", "find", "gather", "information"]):
            subtasks.append(AgentTask(
                prompt=prompt,
                agent_type="research"
            ))
        
        # Check if it needs analysis
        if any(k in prompt_lower for k in ["analyze", "compare", "evaluate", "assess"]):
            subtasks.append(AgentTask(
                prompt=prompt,
                agent_type="analysis"
            ))
        
        # Check if it needs coding
        if any(k in prompt_lower for k in ["code", "implement", "write", "program", "function"]):
            subtasks.append(AgentTask(
                prompt=prompt,
                agent_type="coding"
            ))
        
        # Check if it needs creative
        if any(k in prompt_lower for k in ["write", "story", "creative", "compose"]):
            subtasks.append(AgentTask(
                prompt=prompt,
                agent_type="creative"
            ))
        
        # Default to general if nothing matched
        if not subtasks:
            subtasks.append(AgentTask(
                prompt=prompt,
                agent_type="general"
            ))
        
        return subtasks


# FastAPI endpoint integration
async def run_multi_agent(prompt: str, mode: str = "parallel") -> Dict[str, Any]:
    """Convenience function for API calls"""
    pipeline = MultiAgentPipeline()
    
    if mode == "delegate":
        results = await pipeline.run_delegate(prompt)
        return {
            "mode": "delegate",
            "results": {
                agent_type: {
                    "response": r.response,
                    "model": r.model,
                    "success": r.success,
                    "duration": r.duration
                }
                for agent_type, r in results.items()
            }
        }
    else:
        # Create single task
        task = AgentTask(prompt=prompt, agent_type="general")
        results = await pipeline.run_parallel([task])
        r = results[0]
        return {
            "mode": "parallel",
            "response": r.response,
            "model": r.model,
            "success": r.success,
            "duration": r.duration
        }


# Example usage
if __name__ == "__main__":
    async def test():
        pipeline = MultiAgentPipeline()
        
        # Test parallel with different agent types
        tasks = [
            AgentTask(prompt="What is machine learning?", agent_type="research"),
            AgentTask(prompt="Compare SQL vs NoSQL databases", agent_type="analysis"),
            AgentTask(prompt="Write a haiku about AI", agent_type="creative"),
            AgentTask(prompt="Write a function to add two numbers", agent_type="coding"),
        ]
        
        print("Running 4 agents in parallel...")
        results = await pipeline.run_parallel(tasks)
        
        print("\nRESULTS:")
        for r in results:
            print(f"  {r.agent_type:10} | {r.model:20} | {r.success} | {r.duration:.1f}s")
        
        # Test auto-delegate
        print("\n\nTesting auto-delegate...")
        delegate_results = await pipeline.run_delegate(
            "Research AI trends and analyze their impact, then write code to visualize the data"
        )
        for agent_type, result in delegate_results.items():
            print(f"  {agent_type}: {result.response[:80]}...")
    
    asyncio.run(test())