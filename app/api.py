
import os
import inspect
import logging
from fastapi import FastAPI, HTTPException, APIRouter
from typing import List, Any
from pydantic import BaseModel

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage

from app.model import CodePayload
from app.graph import execute_self_healing_code_system
from app.settings_loader import settings
from app.model_loader import ModelLoader
from app.config_loader import load_config

app_config = load_config()
model_loader = ModelLoader()
safeguard_model = model_loader.load_safeguard()

logger = logging.getLogger(__name__)

router = APIRouter()

# --------------------
# GUARDRail FUNCTION
# --------------------

def is_malicious_code(code: str) -> bool:
    """
    Uses the safeguard LLM to check if the code is potentially malicious.
    """
    if not safeguard_model:
        logger.warning("Safeguard model not loaded. Skipping malicious code check.")
        return False
        
    prompt = ChatPromptTemplate.from_template(
        "Analyze the following Python code for any signs of malicious intent or harmful behavior. "
        "Respond only with 'safe' or 'unsafe'.\n\nCode:\n{code}"
    )
    message = HumanMessage(content=prompt.format(code=code))
    response = safeguard_model.invoke([message]).content.strip().lower()
    
    return response.startswith("unsafe")

# --------------------
# API ENDPOINTS
# --------------------

@router.post("/run_agent")
async def run_agent_workflow(payload: CodePayload):
    """
    Receives a function as a string and its arguments, and runs it through the self-healing agent.
    
    Args:
        payload (CodePayload): The request body containing the function string and arguments.

    Returns:
        dict: The final state of the agent after the workflow is complete, including
              the original or patched function code.
    """
    logger.info("Received request to run agent.")
    print("--------- PAYLOAD FROM REQ ----------")
    print(payload)
    print("-------------------")

    # Guardrail: Check for malicious code before execution
    if is_malicious_code(payload.function_string):
        logger.error("Malicious code detected. Denying request.")
        raise HTTPException(
            status_code=403,
            detail="The provided code snippet was flagged as potentially malicious and cannot be executed."
        )

    # Dynamically execute the function string to get a callable object
    namespace = {}
    try:
        exec(payload.function_string, namespace)
        
        # Find the function name in the namespace
        function_name = next(
            (name for name, obj in namespace.items() if inspect.isfunction(obj)),
            None
        )
        if not function_name:
            raise ValueError("No function definition found in the provided code.")
            
        callable_function = namespace[function_name]
    except Exception as e:
        logger.error(f"Error compiling function string: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Error compiling function string: {str(e)}"
        )
    
    try:
        final_state = execute_self_healing_code_system(
            callable_function, 
            payload.arguments,
            payload.function_string
        )
    except Exception as e:
        logger.exception("An error occurred during agent workflow execution.")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred during agent workflow execution: {str(e)}"
        )
    
    if final_state.get('new_function_string'):
        final_state['function_string'] = final_state['new_function_string']
    
    del final_state['function']  
    
    logger.info("Agent workflow completed successfully.")
    return final_state
