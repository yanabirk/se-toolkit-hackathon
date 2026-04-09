"""Observability tools for querying VictoriaLogs and VictoriaTraces."""

import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from mcp.types import Tool
from pydantic import BaseModel, Field


class LogsSearchQuery(BaseModel):
    query: str = Field(
        description="LogsQL query string (e.g., '_time:10m service.name:\"LMS\" severity:ERROR')"
    )
    limit: int = Field(default=10, description="Max number of log entries to return")


class LogsErrorCountQuery(BaseModel):
    service: str = Field(description="Service name to check for errors")
    minutes: int = Field(default=60, description="Time window in minutes")


class TracesListQuery(BaseModel):
    service: str = Field(description="Service name to list traces for")
    limit: int = Field(default=5, description="Max number of traces to return")


class TracesGetQuery(BaseModel):
    trace_id: str = Field(description="Trace ID to fetch")


ToolPayload = list[dict] | dict


@dataclass(frozen=True, slots=True)
class ToolSpec:
    name: str
    description: str
    model: type[BaseModel]
    handler: Callable

    def as_tool(self) -> Tool:
        schema = self.model.model_json_schema()
        schema.pop("$defs", None)
        schema.pop("title", None)
        return Tool(name=self.name, description=self.description, inputSchema=schema)


async def _logs_search(args: LogsSearchQuery, base_url: str) -> ToolPayload:
    """Search logs using VictoriaLogs LogsQL query."""
    import httpx

    url = f"{base_url}/select/logsql/query"
    params = {"query": args.query, "limit": args.limit}
    try:
        with httpx.Client() as client:
            resp = client.get(url, params=params, timeout=30.0)
            resp.raise_for_status()
            if not resp.text.strip():
                return {"count": 0, "query": args.query, "message": "No logs found"}
            lines = resp.text.strip().split("\n")
            return [json.loads(line) for line in lines if line.strip()]
    except Exception as e:
        return {"error": str(e), "query": args.query, "url": url}


async def _logs_error_count(args: LogsErrorCountQuery, base_url: str) -> ToolPayload:
    """Count errors per service over a time window."""
    import httpx

    query = f'_time:{args.minutes}m service.name:"{args.service}" severity:ERROR'
    url = f"{base_url}/select/logsql/query"
    params = {"query": query, "limit": 1000}
    try:
        with httpx.Client() as client:
            resp = client.get(url, params=params, timeout=30.0)
            resp.raise_for_status()
            if not resp.text.strip():
                return {
                    "count": 0,
                    "service": args.service,
                    "window_minutes": args.minutes,
                    "message": "No errors found",
                }
            lines = resp.text.strip().split("\n")
            logs = [json.loads(line) for line in lines if line.strip()]
            return {
                "count": len(logs),
                "service": args.service,
                "window_minutes": args.minutes,
                "sample_logs": logs[:5],
            }
    except Exception as e:
        return {"error": str(e), "service": args.service, "query": query}


async def _traces_list(args: TracesListQuery, base_url: str) -> ToolPayload:
    """List recent traces for a service."""
    import httpx

    url = f"{base_url}/select/jaeger/api/traces"
    params = {"service": args.service, "limit": args.limit}
    try:
        with httpx.Client() as client:
            resp = client.get(url, params=params, timeout=30.0)
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", [])
    except Exception as e:
        return {"error": str(e), "service": args.service, "url": url}


async def _traces_get(args: TracesGetQuery, base_url: str) -> ToolPayload:
    """Fetch a specific trace by ID."""
    import httpx

    url = f"{base_url}/select/jaeger/api/traces/{args.trace_id}"
    try:
        with httpx.Client() as client:
            resp = client.get(url, timeout=30.0)
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", [{}])[0] if data.get("data") else {}
    except Exception as e:
        return {"error": str(e), "trace_id": args.trace_id, "url": url}


# Tool handlers mapping - uses partial application for base_url
def make_logs_handler(handler):
    return lambda args, url: handler(args, url)


def make_traces_handler(handler):
    return lambda args, url: handler(args, url)


TOOL_SPECS = (
    ToolSpec(
        "obs_logs_search",
        "Search VictoriaLogs using LogsQL query. Use for finding errors, debugging issues.",
        LogsSearchQuery,
        make_logs_handler(_logs_search),
    ),
    ToolSpec(
        "obs_logs_error_count",
        "Count errors for a service over a time window. Use to check if there are recent errors.",
        LogsErrorCountQuery,
        make_logs_handler(_logs_error_count),
    ),
    ToolSpec(
        "obs_traces_list",
        "List recent traces for a service. Use to find trace IDs for debugging.",
        TracesListQuery,
        make_traces_handler(_traces_list),
    ),
    ToolSpec(
        "obs_traces_get",
        "Fetch a specific trace by ID. Use to inspect the full span hierarchy of a request.",
        TracesGetQuery,
        make_traces_handler(_traces_get),
    ),
)

TOOLS_BY_NAME = {spec.name: spec for spec in TOOL_SPECS}
TOOL_HANDLERS = {spec.name: spec.handler for spec in TOOL_SPECS}
