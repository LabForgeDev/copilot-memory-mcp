# copilot-memory-mcp

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Persistent semantic memory for GitHub Copilot in VS Code.

A local MCP server that gives Copilot durable, project-scoped memory across sessions. Memories are stored in an embedded ChromaDB vector database with `all-MiniLM-L6-v2` embeddings, enabling semantic retrieval (RAG). Everything runs in a single Docker container — no cloud services required.

---

## Quick start

```bash
docker compose up -d
```

The server starts on `http://localhost:8000/sse`.

The `.vscode/mcp.json` already points Copilot at the server — no further VS Code configuration needed.

---

## MCP tools

| Tool | Description |
|---|---|
| `create_memory` | Store a new memory with title, content, optional project scope and tags |
| `search_memories` | Semantic vector search; filter by project and/or tags |
| `update_memory` | Update an existing memory by ID; re-embeds on change |
| `delete_memory` | Permanently delete a memory by ID |
| `list_memories` | Browse memories with pagination (lightweight, no content) |

---

## Architecture

```
VS Code / Copilot
      │  MCP HTTP/SSE (port 8000)
      ▼
┌─────────────────────────────────┐
│  Docker Container               │
│                                 │
│  FastMCP Server (port 8000)     │
│    └── 5 MCP tools              │
│                                 │
│  sentence-transformers          │
│    └── all-MiniLM-L6-v2        │
│        (384-dim embeddings)     │
│                                 │
│  ChromaDB (embedded)            │
│    └── collection "memories"   │
└──────────┬──────────────────────┘
           │ Docker named volume
           ▼
    /data/chroma  (persisted DB)
```

---

## Project layout

```
copilot-memory-mcp/
├── app/
│   ├── main.py              # FastMCP server, tool registration
│   ├── memory_store.py      # ChromaDB wrapper (CRUD + search)
│   ├── embeddings.py        # sentence-transformers loader + encode()
│   └── tools/
│       ├── create_memory.py
│       ├── search_memories.py
│       ├── update_memory.py
│       ├── delete_memory.py
│       └── list_memories.py
├── tests/
│   ├── test_memory_store.py
│   └── test_tools.py
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

---

## Development

### Install dependencies

```bash
pip install -e ".[dev]"
```

### Run tests

```bash
pytest
```

Tests use an ephemeral in-memory ChromaDB and a mocked embedding function — no Docker, no model download required.

### Run the server locally (no Docker)

```bash
pip install -e .
PYTHONPATH=. python app/main.py
```

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `SENTENCE_TRANSFORMERS_HOME` | `/app/models` | Model cache directory |
| `CHROMA_PATH` | `/data/chroma` | ChromaDB persistence path |
| `PORT` | `8000` | HTTP server port |

Copy `.env.example` to `.env` and adjust if needed.

---

## License

MIT — see [LICENSE](LICENSE).
