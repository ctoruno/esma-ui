# Esmé - Streamlit Client for LangChain/KLangGraph Agent

This repository contains a **Streamlit-based chat interface** that connects to a **FastAPI server** running a LangChain/KLangGraph agent.  
The app allows users to interact with the agent in natural language, request data analyses, and generate SQL queries for ENAHO (Peru) and GEIH (Colombia) datasets.

---

## 🚀 Features
- Chat-style interface powered by **Streamlit**.
- Connects to a **FastAPI backend** via **Server-Sent Events (SSE)** for real-time streaming responses.
- Manages **conversation state** with session IDs (`thread_id`).
- Provides instructions, status indicators, and session management (start a new conversation).
- Supports debug mode for inspecting raw API responses.

---

## 🛠️ Requirements
- Python 3.9+
- Install dependencies:
  ```bash
  pip install -r requirements.txt
````

---

## ▶️ Running the App

1. Start your FastAPI server that serves the LangChain/KLangGraph agent (make sure it exposes a `/chat/stream` endpoint).

2. Run the Streamlit app:

   ```bash
   streamlit run main.py
   ```

3. Open your browser at [http://localhost:8501](http://localhost:8501).

---

## ⚙️ Configuration

* The app connects to the FastAPI backend via the `BASE_URL` constant in `main.py`.
  Update it if your backend is deployed elsewhere:

  ```python
  BASE_URL = "https://your-fastapi-server.com"
  ```

* Timeout for connections can be adjusted with:

  ```python
  CONNECTION_TIMEOUT = 300.0
  ```

---

## 📂 Project Structure

```
esma-ui
├── cloudbuild.yaml
├── Dockerfile
├── main.py
├── pyproject.toml
├── README.md
├── requirements.txt
├── src
│   ├── __init__.py
│   └── client.py
├── static
└── uv.lock
```

---

## 💡 Notes

* The agent may produce incorrect responses; provide clear and precise prompts for better results.
* Debug mode can be enabled in `main.py` to inspect raw API responses.

---

## 🖥️ Example Use

* Ask natural language questions about **ENAHO** or **GEIH** data.
* Generate **statistics**, **summaries**, or **SQL queries**.
* Stream real-time answers from the LangChain/KLangGraph agent.

---
