# File: frontend.py
import streamlit as st
import json
import logging
import inspect

# --- NEW IMPORTS (from your api.py and backend logic) ---
from app.graph import execute_self_healing_code_system
from app.model_loader import ModelLoader
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CACHING FOR PERFORMANCE ---
# This uses Streamlit's cache to load the model only once, preventing
# it from reloading on every user interaction.
@st.cache_resource
def get_safeguard_model():
    """Loads and caches the safeguard model."""
    logger.info("Loading safeguard model...")
    model_loader = ModelLoader()
    return model_loader.load_safeguard()

# Load the model using the cached function
safeguard_model = get_safeguard_model()

# --- LOGIC MOVED FROM API.PY ---
# This function is now part of the Streamlit app.
def is_malicious_code(code: str) -> bool:
    """Uses the safeguard LLM to check if the code is potentially malicious."""
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

# --------------------------------------------------------------------------
# --- STREAMLIT UI CODE (Mostly unchanged) ---
# --------------------------------------------------------------------------

st.set_page_config(
    page_title="Self-Healing Code Agent",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🤖 Self-Healing Code Agent")
st.markdown("Enter a Python function and its arguments to have the agent find and fix bugs.")

# Input for the function code
st.subheader("Python Function Code")
function_string = st.text_area(
    "Paste your function here:",
    height=200,
    value="def divide_numbers(a, b):\n    return a / b"
)

# Input for the function arguments
st.subheader("Function Arguments (as JSON array)")
arguments_string = st.text_area(
    "Enter a list of arguments for your function:",
    height=100,
    value="[10, 0]"
)

# --------------------------------------------------------------------------
# --- REFACTORED BUTTON LOGIC ---
# --------------------------------------------------------------------------
# This block now contains all the backend logic instead of making an API call.
if st.button("Run Agent", type="primary"):
    if not function_string or not arguments_string:
        st.error("Please provide both a function and arguments.")
    else:
        try:
            # 1. Parse arguments from the UI
            arguments = json.loads(arguments_string)
            
            with st.spinner("Running agent workflow..."):
                # 2. Guardrail: Check for malicious code first
                if is_malicious_code(function_string):
                    st.error("The provided code was flagged as potentially malicious and cannot be executed.")
                    st.stop() # Stop execution

                # 3. Dynamically prepare the function from the string
                namespace = {}
                exec(function_string, namespace)
                function_name = next(
                    (name for name, obj in namespace.items() if inspect.isfunction(obj)), None
                )
                
                if not function_name:
                    st.error("No function definition found in the provided code.")
                    st.stop()
                    
                callable_function = namespace[function_name]

                # 4. Execute the main agent logic directly
                final_state = execute_self_healing_code_system(
                    callable_function, 
                    arguments,
                    function_string
                )
                
                # Clean up the state object for display
                if final_state.get('function'):
                    del final_state['function']

            # 5. Display the results (this part is the same as before)
            st.success("✅ Agent workflow completed successfully!")
            st.subheader("Results")
            
            st.info("The agent started with this function:")
            st.code(function_string, language='python')
            
            patched_code = final_state.get('new_function_string')
            if patched_code:
                st.success("The agent applied the following fix:")
                st.code(patched_code, language='python')
            
            if not final_state.get('error'):
                final_result = final_state.get('result', 'No result returned.')
                st.success(f"Final Result: {final_result}")
            else:
                st.error(f"Final Error: {final_state.get('error_description')}")
                
            st.markdown("### 📝 Bug Report from the Agent")
            st.text(final_state.get('bug_report', 'No bug report generated.'))

        except json.JSONDecodeError:
            st.error("Invalid JSON format for arguments. Please enter a valid JSON array.")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            logger.exception("An error occurred during agent workflow execution.")