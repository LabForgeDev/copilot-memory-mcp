"""FastMCP server entrypoint — registers all 5 memory tools."""
from __future__ import annotations

import logging
import os

from fastmcp import FastMCP

from app.tools.create_memory import create_memory
from app.tools.delete_memory import delete_memory
from app.tools.list_memories import list_memories
from app.tools.search_memories import search_memories
from app.tools.update_memory import update_memory

logging.basicConfig(level=logging.INFO)

mcp = FastMCP("copilot-memory-mcp")

mcp.tool()(create_memory)
mcp.tool()(search_memories)
mcp.tool()(update_memory)
mcp.tool()(delete_memory)
mcp.tool()(list_memories)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    mcp.run(transport="sse", host="0.0.0.0", port=port)
