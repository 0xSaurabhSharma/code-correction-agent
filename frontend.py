# File: streamlit_app.py
import streamlit as st
import requests
import json
import logging
import subprocess
import time
import os

# --- Launch the FastAPI Backend ---
# This is the core workaround. It starts the Uvicorn server in a separate process.
# We check if it's already running to prevent multiple instances.
try:
    requests.get("http://localhost:8000")
    st.info("FastAPI service is already running.")
except requests.exceptions.ConnectionError:
    st.info("Starting FastAPI service...")
    
    # Use a subprocess to run the uvicorn command
    # `shell=True` is needed for the command to be executed correctly on some systems
    p = subprocess.Popen(
        [
            "uvicorn", "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ],
        cwd=os.getcwd(), # Set the current working directory to the project root
    )
    
    # Wait for the server to be ready
    time.sleep(5)
    st.info("FastAPI service started!")


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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

# --- Determine the API URL dynamically ---
# In a single container, the FastAPI service runs on localhost
# On your local machine, it's also localhost
BASE_URL = "http://localhost:8000"

# Button to trigger the agent
if st.button("Run Agent", type="primary"):
    if not function_string or not arguments_string:
        st.error("Please provide both a function and arguments.")
    else:
        try:
            # Parse the arguments from the JSON string
            arguments = json.loads(arguments_string)
            
            # Construct the payload to send to the FastAPI backend
            payload = {
                "function_string": function_string,
                "arguments": arguments
            }
            
            # Display a spinner while the agent is working
            with st.spinner("Running agent workflow..."):
                # Send the POST request to the FastAPI endpoint
                response = requests.post(f"{BASE_URL}/run_agent", json=payload)
            
            # Check for a successful response
            if response.status_code == 200:
                final_state = response.json()
                st.success("✅ Agent workflow completed successfully!")
                
                # Display the results
                st.subheader("Results")
                
                # Show the original function code
                st.info("The agent started with this function:")
                st.code(function_string, language='python')
                
                # Show the patched function if a fix was applied
                patched_code = final_state.get('new_function_string')
                if patched_code:
                    st.success("The agent applied the following fix:")
                    st.code(patched_code, language='python')
                
                # Display the final execution result
                if not final_state['error']:
                    st.success(f"Final Result: {final_state.get('function_string')}")
                else:
                    st.error(f"Final Error: {final_state.get('error_description')}")
                    
                # Display the full bug report
                st.markdown("### 📝 Bug Report from the Agent")
                st.markdown(f"```\n{final_state.get('bug_report')}\n```")
                
            else:
                st.error(f"API Error: {response.status_code}")
                st.json(response.json())
                
        except json.JSONDecodeError:
            st.error("Invalid JSON format for arguments. Please enter a valid JSON array.")
        except requests.exceptions.ConnectionError:
            st.error("Connection Error: Is the FastAPI server running?")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
