# GitHub Copilot Instructions — Memory Tools

You have access to a persistent memory MCP server (`copilot-memory`) at `http://localhost:8000/sse`.

## Available tools

| Tool | When to use |
|---|---|
| `create_memory` | Save a new decision, convention, or finding |
| `search_memories` | Retrieve relevant context before answering |
| `update_memory` | Amend an existing memory when something changes |
| `delete_memory` | Remove stale or incorrect memories |
| `list_memories` | Browse all saved memories for a project |

## Rules

1. **Always search before answering** questions about architecture, conventions, or past decisions — call `search_memories` first.
2. **Always save** new architectural decisions, agreed conventions, and non-obvious workarounds.
3. **Set `project_name`** to the current repository name on every call.
4. **Prefer `update_memory`** over delete + recreate when content changes.
5. **Use consistent tags**: `architecture`, `convention`, `bug`, `performance`, `devops`, `security`, `testing`, `tooling`.
6. **Do not save** temporary debug notes or information already obvious from the code.
