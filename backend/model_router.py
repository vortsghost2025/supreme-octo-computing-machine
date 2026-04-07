"""
Model Router - automatically routes requests to the best model based on task complexity
"""
import os
from typing import Optional, Dict, Any

class ModelRouter:
    """Routes requests to optimal model based on task type."""
    
    # Model configurations
    MODELS = {
        "fast": {
            "name": "orca-mini:latest",
            "context": 2048,
            "description": "Fast, lightweight for simple tasks"
        },
        "balanced": {
            "name": "mistral:7b", 
            "context": 4096,
            "description": "Good balance of speed and quality"
        },
        "quality": {
            "name": "llama3:8b-instruct-q4_K_M",
            "context": 4096,
            "description": "Best quality for complex reasoning (quantized)"
        }
    }
    
    # Task keywords for routing
    TASK_ROUTING = {
        "fast": ["simple", "quick", "list", "what is", "when", "who", "count", "yes", "no"],
        "balanced": ["explain", "describe", "write", "summarize", "compare", "convert", "calculate"],
        "quality": ["analyze", "reason", "think", "complex", "debug", "architecture", "design", "implement"]
    }
    
    def __init__(self):
        self.default_model = os.getenv("DEFAULT_MODEL", "balanced")
    
    def route(self, prompt: str, requested_model: Optional[str] = None) -> Dict[str, Any]:
        """Route prompt to optimal model."""
        
        # If user specifies a model, use it
        if requested_model:
            return {
                "model": requested_model,
                "context": self._get_context(requested_model),
                "routing": "user_specified"
            }
        
        # Auto-route based on prompt analysis
        prompt_lower = prompt.lower()
        
        # Check for fast tasks
        if any(kw in prompt_lower for kw in self.TASK_ROUTING["fast"]):
            return {
                "model": self.MODELS["fast"]["name"],
                "context": self.MODELS["fast"]["context"],
                "routing": "auto_fast"
            }
        
        # Check for quality tasks
        if any(kw in prompt_lower for kw in self.TASK_ROUTING["quality"]):
            return {
                "model": self.MODELS["quality"]["name"],
                "context": self.MODELS["quality"]["context"],
                "routing": "auto_quality"
            }
        
        # Default to balanced
        return {
            "model": self.MODELS[self.default_model]["name"],
            "context": self.MODELS[self.default_model]["context"],
            "routing": "auto_balanced"
        }
    
    def _get_context(self, model: str) -> int:
        """Get context size for a model."""
        for tier in self.MODELS.values():
            if tier["name"] == model:
                return tier["context"]
        return 4096
    
    def list_models(self) -> Dict[str, Any]:
        """List available models and their configs."""
        return self.MODELS

# Singleton
router = ModelRouter()

def route_request(prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function for routing."""
    return router.route(prompt, model)