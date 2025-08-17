

import streamlit as st
import requests
import json
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


st.set_page_config(
    page_title="Self-Healing Code Agent",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🤖 Self-Healing Code Agent")
st.markdown("Enter a Python function and its arguments to have the agent find and fix bugs.")


st.subheader("Python Function Code")
function_string = st.text_area(
    "Paste your function here:",
    height=200,
    value="def divide_numbers(a, b):\n    return a / b"
)


st.subheader("Function Arguments (as JSON array)")
arguments_string = st.text_area(
    "Enter a list of arguments for your function:",
    height=100,
    value="[10, 0]"
)


if st.button("Run Agent", type="primary"):
    if not function_string or not arguments_string:
        st.error("Please provide both a function and arguments.")
    else:
        try:
            
            arguments = json.loads(arguments_string)
            
            
            payload = {
                "function_string": function_string,
                "arguments": arguments
            }
            
            
            with st.spinner("Running agent workflow..."):
                
                response = requests.post("http://127.0.0.1:8000/run_agent", json=payload)
            
            
            if response.status_code == 200:
                final_state = response.json()
                st.success("✅ Agent workflow completed successfully!")
                
                
                st.subheader("Results")
                
                
                st.info("The agent started with this function:")
                st.code(function_string, language='python')
                
                
                patched_code = final_state.get('new_function_string')
                if patched_code:
                    st.success("The agent applied the following fix:")
                    st.code(patched_code, language='python')
                
                
                if not final_state['error']:
                    st.success(f"Final Result: {final_state.get('function_string')}")
                else:
                    st.error(f"Final Error: {final_state.get('error_description')}")
                    
                
                st.markdown("### 📝 Bug Report from the Agent")
                st.markdown(f"```\n{final_state.get('bug_report')}\n```")
                
            else:
                st.error(f"API Error: {response.status_code}")
                st.json(response.json())
                
        except json.JSONDecodeError:
            st.error("Invalid JSON format for arguments. Please enter a valid JSON array.")
        except requests.exceptions.ConnectionError:
            st.error("Connection Error: Is the FastAPI server running on http://127.0.0.1:8000?")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")

