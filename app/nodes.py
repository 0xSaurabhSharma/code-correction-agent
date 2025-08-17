import uuid
import inspect
import logging
import re
from typing import TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage
from langgraph.graph import END
from langchain_core.documents import Document

from app.model import AgentState
from app.db import VectorDB
from app.model_loader import ModelLoader
from app.settings_loader import settings
from app.config_loader import load_config

app_config = load_config()
model_loader = ModelLoader()
llm = model_loader.load_llm()
embedding_model = model_loader.load_embedding(provider='openai')


if embedding_model:
    db_client = VectorDB(embedding_function=embedding_model)
else:
    db_client = None
    logging.error("Embedding model not loaded, vector database will not be available.")

collection = db_client.get_collection() if db_client else None


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# --------------------
# NODE FUNCTIONS
# --------------------

def code_execution_node(state: AgentState) -> AgentState:
    """Executes the user-provided function and updates the state."""
    logger.info("Executing arbitrary function.")
    try:
        result = state['function'](*state['arguments'])
        logger.info(f"Function ran without error. Result: {result}")
        state['error'] = False
        state['error_description'] = ''
    except Exception as e:
        logger.error(f"Function raised an error: {e}")
        state['error'] = True
        state['error_description'] = str(e)
    return state

def bug_report_node(state: AgentState) -> AgentState:
    """Generates a comprehensive bug report using the LLM."""
    logger.info("Generating bug report.")
    prompt = ChatPromptTemplate.from_template(
        'You are tasked with generating a bug report for a Python function that raised an error.'
        'Function: {function_string}'
        'Error: {error_description}'
        'Your response must be a comprehensive string including only crucial information on the bug report'
    )
    message = HumanMessage(content=prompt.format(
        function_string=state['function_string'], 
        error_description=state['error_description']
    ))
    bug_report = llm.invoke([message]).content.strip()
    logger.info(f"Generated bug report: {bug_report}")
    state['bug_report'] = bug_report
    return state

def memory_search_node(state: AgentState) -> AgentState:
    """Searches the ChromaDB vector database for similar bug reports."""
    if not collection:
        logger.error("Collection is not initialized. Skipping memory search.")
        state['memory_search_results'] = []
        return state

    logger.info("Searching for relevant bug reports in memory.")
    prompt = ChatPromptTemplate.from_template(
        'You are tasked with archiving a bug report for a Python function that raised an error.'
        'Bug Report: {bug_report}.'
        'Your response must be a concise string including only crucial information on the bug report for future reference.'
        'Format: # function_name ## error_description ### error_analysis'
    )
    message = HumanMessage(content=prompt.format(bug_report=state['bug_report']))
    response = llm.invoke([message]).content.strip()
    
    try:
        results = collection.similarity_search_with_score(query=response, k=10)
    except Exception as e:
        logger.error(f"ChromaDB query failed: {e}")
        results = []
        
    if results:
        logger.info(f"Found {len(results)} similar bug reports.")
        state['memory_search_results'] = [
            {'id': doc.metadata.get('id', str(uuid.uuid4())), 'memory': doc.page_content, 'distance': score} 
            for doc, score in results
        ]
    else:
        logger.info("No similar bug reports found.")
        state['memory_search_results'] = []
        
    return state

def memory_filter_node(state: AgentState) -> AgentState:
    """Filters the search results based on a distance threshold."""
    logger.info("Filtering bug reports.")
    state['memory_ids_to_update'] = []
    for memory in state['memory_search_results']:
        if memory['distance'] < 0.3:
            state['memory_ids_to_update'].append(memory['id'])
    
    logger.info(f"Selected {len(state['memory_ids_to_update'])} bug reports for modification.")
    return state

def memory_generation_node(state: AgentState) -> AgentState:
    """Generates a new memory and stores it in the vector database."""
    if not collection:
        logger.error("Collection is not initialized. Skipping memory generation.")
        return state

    logger.info("Generating and saving a new bug report to memory.")
    prompt = ChatPromptTemplate.from_template(
        'You are tasked with archiving a bug report for a Python function that raised an error.'
        'Bug Report: {bug_report}.'
        'Your response must be a concise string including only crucial information on the bug report for future reference.'
        'Format: # function_name ## error_description ### error_analysis'
    )
    message = HumanMessage(content=prompt.format(bug_report=state['bug_report']))
    response = llm.invoke([message]).content.strip()
    
    new_id = str(uuid.uuid4())
    doc = Document(page_content=response, metadata={"id": new_id})
    collection.add_documents(documents=[doc], ids=[new_id])
    logger.info(f"Saved new bug report to memory with ID: {new_id}")
    return state

def memory_modification_node(state: AgentState) -> AgentState:
    """Updates a prior memory with new information based on the current bug report."""
    if not collection:
        logger.error("Collection is not initialized. Skipping memory modification.")
        return state

    logger.info("Modifying existing bug report in memory.")
    prompt = ChatPromptTemplate.from_template(
        'Update the following memories based on the new interaction:'
        'Current Bug Report: {bug_report}'
        'Prior Bug Report: {memory_to_update}'
        'Your response must be a concise but cumulative string including only crucial information on the current and prior bug reports for future reference.'
        'Format: # function_name ## error_description ### error_analysis'
    )
    memory_to_update_id = state['memory_ids_to_update'].pop(0)
    results = collection.get(ids=[memory_to_update_id])

    if results['documents']:
        memory_to_update = results['documents'][0]
    else:
        logger.warning(f"Could not retrieve document with ID {memory_to_update_id}. Skipping modification.")
        return state

    message = HumanMessage(content=prompt.format(
        bug_report=state['bug_report'],
        memory_to_update=memory_to_update,
    ))
    response = llm.invoke([message]).content.strip()
    
    updated_doc = Document(page_content=response, metadata={"id": memory_to_update_id})
    collection.update_documents(ids=[memory_to_update_id], documents=[updated_doc])
    logger.info(f"Updated memory with ID: {memory_to_update_id}")
    return state

def code_update_node(state: AgentState) -> AgentState:
    """Generates a proposed bug fix using the LLM."""
    logger.info("Generating proposed bug fix.")
    prompt = ChatPromptTemplate.from_template(
        'You are tasked with fixing a Python function that raised an error.'
        'Function: {function_string}'
        'Error: {error_description}' 
        'You must provide a fix for the present error only.'
        'The bug fix should handle the thrown error case gracefully by returning an error message.'
        'Do not raise an error in your bug fix.'
        'The function must use the exact same name and parameters.'
        'Your response must contain only the function definition with no additional text.'
        'Your response must not contain any additional formatting, such as code delimiters or language declarations.'
    )
    message = HumanMessage(content=prompt.format(
        function_string=state['function_string'], 
        error_description=state['error_description']
    ))
    new_function_string = llm.invoke([message]).content.strip()
    
    logger.info(f"Proposed bug fix: {new_function_string}")
    state['new_function_string'] = new_function_string
    return state

def code_patching_node(state: AgentState) -> AgentState:
    """Applies the proposed fix and tests the patched function."""
    logger.info("Applying code patch.")
    try:
        # print("---------------- STATE IN PATCHING -------------------")
        # for key, value in state.items():
        #     print(f"Key: {key}, Value: {value}")
        # print("-----------------------------------")
        
        # Remove Markdown code fences from the LLM's response
        new_code = re.sub(r'```python\n|```', '', state['new_function_string']).strip()
        
        namespace = {}
        exec(new_code, namespace)
        
        func_name = state['function'].__name__
        new_function = namespace[func_name]
        
        state['function'] = new_function
        state['error'] = False
        
        # Test the patched function with the original arguments
        result = state['function'](*state['arguments'])
        logger.info(f"Patch successful. Test run result: {result}")
    except Exception as e:
        logger.error(f"Patch failed: {e}")
        state['error'] = True
    return state

# --------------------
# ROUTER FUNCTIONS
# --------------------

def error_router(state: AgentState) -> str:
    """Decides if the workflow should proceed to fix the error or end."""
    return 'bug_report_node' if state['error'] else END

def memory_filter_router(state: AgentState) -> str:
    """Decides if similar memories were found."""
    return 'memory_filter_node' if state['memory_search_results'] else 'memory_generation_node'

def memory_generation_router(state: AgentState) -> str:
    """Decides if there are memories to update."""
    return 'memory_modification_node' if state['memory_ids_to_update'] else 'memory_generation_node'

def memory_update_router(state: AgentState) -> str:
    """Decides if there are more memories to update."""
    return 'memory_modification_node' if state['memory_ids_to_update'] else 'code_update_node'
