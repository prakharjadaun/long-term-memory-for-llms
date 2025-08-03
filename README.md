# Long Term Memory For LLMs 🚀

**A modular, production-ready agent framework providing persistent user memories in GPT‑based chats via function‑calling and Azure Cognitive Search.**

---

## 🧩 Problem Statement

Modern conversational agents powered by GPT (OpenAI or Azure OpenAI) are stateless beyond a single session. They can:
- Forget _personal preferences_ shared by the user.
- Lose context beyond the model's token window.
- Hallucinate by repeating outdated assumptions or ignoring updates.

---

## 💡 Solution Overview

A multi-stage agent that:

1. Uses **function calling** to delegate memory tasks (add/search/delete).
2. Stores “facts” in a **vector‑based semantic index** via **Azure Cognitive Search** (with HNSW + KNN + semantic profiles).
3. Triggers memory writes automatically via **token‑threshold detection**.
4. Provides a stylish **Chainlit UI** with streaming, visual tool‑steps, and full traceability.
5. Supports both **OpenAI** and **Azure OpenAI** behind a unified `Provider` interface.

This ensures your assistant **remembers, updates, and reasons** across chat threads with minimal manual bookkeeping.

---

## 🧱 Architecture & Workflow

```plaintext
User → assistant + context → Memory Agent
                         ↙          ↘
                      APIs & Tools   Memory Reads
                      (tools calls)  ↺ LLM Responses

```

1. Chainlit UI Layer: Listens to user, maintains visible message history, and initializes the agent.
2. Internal Agent Loop:
   - Appends each user message to internal_history.
   - Calls GPT with tool_choice="auto" and streaming.
   - Reads tool_calls and executes them at most once.
3. Tool Support:
   - `check_token_count`: Measures token usage; triggers memory write when over threshold.
   - `add_memory`: Summarizes and inserts memory documents (id, memory string, embeddings, category, timestamp).
   - `search_memory`: Retrieves existing memory based on similarity and category filter.
   - `delete_memory`: Removes outdated memory entries by their ids.
4. Azure Cognitive Search:
   - Maintains an index with vector-search and semantic ranking features (Indexed via HNSW + exhaustive KNN).
   - Supports filters (e.g. memory category, date range, user id) efficiently through Azure AI Search’s indexing and query language.
5. Overflow Handling: When conversations exceed the token limit, older messages are compressed via memory summary and stored; only essential context remains.

## 🧰 Tools & Technologies

- LLMs: Supports both gpt‑4o, gpt‑3.5‑turbo‑16k, azure/gpt‑4o‑mini, etc.
- Function‑Calling Interface: GPT decides when to trigger the tools with predefined tool schemas
- Vector Database: Azure Cognitive Search with vector‑profiles, HNSW and KNN configurations for fast/similar retrieval.
- Async Support: Fully async design using asyncopenai/asyncazureopenai, and async version of Azure Search client.
- Configuration & Validation: pydantic for loading/validating .env and llm_config.yaml.
- Logging: loguru used across providers and memory handlers.
- Chainlit UI: Multi-step streaming interface with visible function/tool calls and authentication support.

## ✅ Project Features

- Support for both OpenAI and Azure OpenAI, selected via config.
- Async providers abstract over both services for embedding and chat completion.
- Schema-validated configs (pydantic) from .env and llm_config.yaml.
- Semantic memory pipeline—includes add/update/search/delete with Azure Search.
- Auto‑summarizing memory when token limits exceed, using full-chain prompting.
- Chainlit interface:
  - Streaming token‑by‑token assistant replies.
  - Visual tool‑steps for function calls like “add_memory” and “search_memory”.
  - Admin/password auth support (by ENV variables).
- Code layout supports separation of concerns:<br>
    /prompts, /tools, /providers, /memory_handler, /agents, /llm_handler.

## **Setup**

<details>

<summary>Click to expand the setup instructions</summary>

I have utilized conda to create and manage the environments.

1. Environment creation

    ```sh
    conda create -n long_term_llm_memory python==3.12 -y
    ```

2. Activate your environment.

    ```sh
    conda activate long_term_llm_memory
    ```

3. Install poetry.

    ```py
    pip install poetry
    ```

   > if pip shows any error for example `Unable to create process using ....` use the below command

   ```py
   python -m pip install --upgrade --force-reinstall pip
   ```

4. Setup the project/package.

    ```sh
    poetry install
    ```

5. Perform the selection of the llm, currently the project supports OPENAI API or Azure OpenAI endpoints and embedding models.

    > llm_config.yaml

6. Run the chainlit app.

   ```sh
   chainlit run app.py -w
   ```

</details>