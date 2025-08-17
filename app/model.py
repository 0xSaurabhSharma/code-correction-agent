from pydantic import BaseModel
from typing import TypedDict, List, Any, Callable, Optional

# --------------------
# Agent Workflow Models
# --------------------

class CodePayload(BaseModel):
    """
    Pydantic model for validating the incoming request body.
    """
    function_string: str
    arguments: List[Any]

class AgentState(TypedDict):
    """
    Represents the state of the agent's workflow.
    
    This TypedDict defines all the keys that will be passed between nodes.
    Using a TypedDict provides a clear and type-safe way to manage state.
    """
    function: Callable
    function_string: str
    arguments: list
    error: bool
    error_description: str
    new_function_string: str
    bug_report: str
    memory_search_results: List[dict]
    memory_ids_to_update: List[str]
