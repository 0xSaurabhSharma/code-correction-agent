# 🤖 Self-Healing Code Agent

This project introduces a sophisticated, AI-powered agent capable of autonomously detecting, diagnosing, and correcting errors in Python code. By leveraging a multi-stage graph-based workflow and a long-term memory system, this agent can learn from past mistakes and continuously improve its bug-fixing capabilities. It's a powerful demonstration of how autonomous agents can enhance developer productivity and code reliability.

## ⚙️ Core Concept: Autonomous Code Correction

The agent operates on a state machine orchestrated by **LangGraph**. When a function fails, the agent initiates a multi-step process to resolve the issue:

### Workflow Diagram

### The Flow Explained:

1.  **💻 Code Execution**: The agent begins by running the user-provided Python function.
2.  **🐞 Error Detection**: If the function throws an error, the agent transitions to the bug analysis phase.
3.  **📝 Bug Report Generation**: An LLM is used to generate a detailed bug report, analyzing the function and the error it produced.
4.  **🧠 Memory Search**: The agent searches its vector database (ChromaDB) for similar, previously encountered bugs.
5.  **💡 Solution Generation & Code Patching**: Drawing insights from its memory and the current bug report, the agent generates a potential fix. This "patch" is then applied to the original function.
6.  **✅ Validation**: The agent re-executes the patched function. If it runs successfully, the process concludes. If not, the cycle continues, refining the solution.

-----

## 🛠️ Tech Stack

  * **Orchestration**: `LangGraph`
  * **LLM Integration**: `LangChain`
  * **Web Framework**: `FastAPI`
  * **Frontend**: `Streamlit`
  * **Vector Database**: `ChromaDB`
  * **LLM Providers**: `OpenAI`, `Google`, `Groq`

-----

## 🚀 Getting Started

### 1\. Clone the Repository

```bash
git clone <your-repository-url>
cd code-correction-agent
```

### 2\. Set Up Environment Variables

Create a `.env` file in the project's root directory and add your API keys:

```env
OPENAI_API_KEY="sk-..."
GROQ_API_KEY="gsk_..."
GOOGLE_API_KEY="AIza..."
```

### 3\. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4\. Run the Application

```bash
streamlit run frontend.py
```
