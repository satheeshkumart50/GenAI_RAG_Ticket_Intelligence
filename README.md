# GenAI_RAG_Ticket_Intelligence
A GenAI-powered Retrieval-Augmented Generation (RAG) system for analyzing telecom Remedy-style ticket data using hybrid SQL and vector retrieval. The platform enables accurate analytics and contextual insights through natural language queries.

What This Project Does
 - Combines SQL-based analytics with semantic vector search
 - Implements a structured RAG data pipeline (chunking + embeddings)
 - Uses an LLM-driven agent to decide between SQL and vector tools
 - Provides conversational analytics via a Streamlit chat UI
 - Enforces accuracy: no LLM guessing, database-backed answers only

Architecture (High Level)
  User → Streamlit UI → GenAI Agent (LangChain Memory)
          → MCP Client → MCP Server
               ├─ SQL_TOOL → PostgreSQL
               └─ VECTOR_TOOL → pgvector (HNSW)

Tech Stack
  - Language: Python
  - Database: PostgreSQL + pgvector
  - LLM: Google Gemini (cloud) / Local LLMs (on-prem)
  - Embeddings: Local embedding models via Ollama
  - Frameworks: LangChain, Streamlit
  - Architecture: MCP (Model Context Protocol) implemented using FastAPI

Key Design Principles
  - SQL for accuracy, vector search for context
  - Tool-based agent orchestration
  - Modular, extensible architecture

Use Cases
  - Telecom incident trend analysis
  - Region, hub, and node-level insights
  - Ticket-to-CR correlation
  - Semantic exploration of historical incidents
  - Conversational analytics for operations teams

Author
Sathish Kumar T
Cloud-Native Architect | GenAI & RAG Systems | Data Engineering
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
<img width="1412" height="653" alt="image" src="https://github.com/user-attachments/assets/5a4a9cfb-6022-4000-bbef-6e2ddc5e9c82" />

<img width="1650" height="505" alt="image" src="https://github.com/user-attachments/assets/2e797b29-fd10-4a52-a8fd-4b5d074ffe95" />

