---
mode: agent
description: Save an important decision, convention, or finding to persistent memory
tools:
  - create_memory
  - update_memory
  - search_memories
---

Before saving, search for an existing memory on this topic to avoid duplicates:
`search_memories` with the key terms from the user's message.

If a closely related memory already exists, use `update_memory` to extend it.
Otherwise, use `create_memory` with:
- A concise, descriptive `title`
- The full context in `content` — include *why*, not just *what*
- `project_name` set to the current project
- Relevant `tags` from: `architecture`, `convention`, `bug`, `performance`, `devops`, `security`, `testing`, `tooling`

Confirm what was saved and its ID to the user.
