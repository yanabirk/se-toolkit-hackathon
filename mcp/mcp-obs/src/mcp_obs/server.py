"""Stdio MCP server exposing observability operations as typed tools."""

import asyncio
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool
from pydantic import BaseModel

from mcp_obs.observability import (
    TOOL_HANDLERS,
    TOOL_SPECS,
    TOOLS_BY_NAME,
)


def _text(data) -> list[TextContent]:
    if isinstance(data, BaseModel):
        payload = data.model_dump()
    else:
        payload = data
    return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False))]


def create_server(logs_url: str, traces_url: str) -> Server:
    server = Server("observability")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [spec.as_tool() for spec in TOOL_SPECS]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict[str, Any] | None
    ) -> list[TextContent]:
        spec = TOOLS_BY_NAME.get(name)
        if spec is None:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
        try:
            args = spec.model.model_validate(arguments or {})
            handler = TOOL_HANDLERS[spec.name]
            # Route to correct base URL based on tool prefix
            if spec.name.startswith("obs_logs"):
                result = await handler(args, logs_url)
            else:
                result = await handler(args, traces_url)
            return _text(result)
        except Exception as exc:
            return [
                TextContent(type="text", text=f"Error: {type(exc).__name__}: {exc}")
            ]

    _ = list_tools, call_tool
    return server


async def main(logs_url: str | None = None, traces_url: str | None = None) -> None:
    import os

    # Read from environment variables or use defaults
    logs_url = logs_url or os.environ.get(
        "VICTORIALOGS_URL", "http://victorialogs:9428"
    )
    traces_url = traces_url or os.environ.get(
        "VICTORIATRACES_URL", "http://victoriatraces:10428"
    )

    server = create_server(logs_url, traces_url)
    async with stdio_server() as (read_stream, write_stream):
        init_options = server.create_initialization_options()
        await server.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    asyncio.run(main())
