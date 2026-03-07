---
mode: agent
description: Search and summarise relevant memories for the current task
tools:
  - search_memories
  - list_memories
---

Search memory for context relevant to the user's question or task.

1. Run `search_memories` with the key concepts from the user's message
2. If `project_name` is known, scope the search to that project first; then run a global search if results are thin
3. Summarise what you found — highlight anything that directly affects the current task
4. If nothing relevant is found, say so clearly and suggest what to save for next time
