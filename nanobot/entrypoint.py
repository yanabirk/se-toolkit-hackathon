#!/usr/bin/env python3
"""Entrypoint for nanobot gateway in Docker.

Resolves environment variables into config at runtime, then launches nanobot gateway.
"""

import json
import os
import sys
from pathlib import Path


def resolve_config():
    """Read config.json, override with env vars, write config.resolved.json."""
    config_path = Path(__file__).parent / "config.json"
    # Write resolved config to /tmp to avoid permission issues
    resolved_path = Path("/tmp") / "nanobot.config.resolved.json"

    with open(config_path) as f:
        config = json.load(f)

    # Override LLM provider settings from env vars
    llm_api_key = os.environ.get("LLM_API_KEY")
    llm_api_base = os.environ.get("LLM_API_BASE_URL")
    llm_api_model = os.environ.get("LLM_API_MODEL")

    if llm_api_key:
        config.setdefault("providers", {}).setdefault("custom", {})["apiKey"] = (
            llm_api_key
        )
    if llm_api_base:
        config.setdefault("providers", {}).setdefault("custom", {})["apiBase"] = (
            llm_api_base
        )
    if llm_api_model:
        config.setdefault("agents", {}).setdefault("defaults", {})["model"] = (
            llm_api_model
        )

    # Override gateway settings from env vars
    gateway_host = os.environ.get("NANOBOT_GATEWAY_CONTAINER_ADDRESS")
    gateway_port = os.environ.get("NANOBOT_GATEWAY_CONTAINER_PORT")

    if gateway_host or gateway_port:
        config.setdefault("gateway", {})
        if gateway_host:
            config["gateway"]["host"] = gateway_host
        if gateway_port:
            config["gateway"]["port"] = int(gateway_port)

    # Override webchat channel settings from env vars
    webchat_host = os.environ.get("NANOBOT_WEBCHAT_CONTAINER_ADDRESS")
    webchat_port = os.environ.get("NANOBOT_WEBCHAT_CONTAINER_PORT")

    if webchat_host or webchat_port:
        config.setdefault("channels", {})
        if "webchat" not in config["channels"]:
            config["channels"]["webchat"] = {
                "enabled": True,
                "allowFrom": ["*"],
            }
        if webchat_host:
            config["channels"]["webchat"]["host"] = webchat_host
        if webchat_port:
            config["channels"]["webchat"]["port"] = int(webchat_port)
    elif "webchat" not in config.get("channels", {}):
        config.setdefault("channels", {})["webchat"] = {
            "enabled": True,
            "host": "0.0.0.0",
            "port": 8765,
            "allowFrom": ["*"],
        }

    # Configure MCP servers from env vars
    lms_backend_url = os.environ.get("NANOBOT_LMS_BACKEND_URL")
    lms_api_key = os.environ.get("NANOBOT_LMS_API_KEY")

    if "mcpServers" not in config.get("tools", {}):
        config.setdefault("tools", {})["mcpServers"] = {}

    # LMS MCP server
    if lms_backend_url or lms_api_key:
        config["tools"]["mcpServers"]["lms"] = {
            "command": "python",
            "args": ["-m", "mcp_lms"],
            "env": {},
        }
        if lms_backend_url:
            config["tools"]["mcpServers"]["lms"]["env"]["NANOBOT_LMS_BACKEND_URL"] = (
                lms_backend_url
            )
        if lms_api_key:
            config["tools"]["mcpServers"]["lms"]["env"]["NANOBOT_LMS_API_KEY"] = (
                lms_api_key
            )

    # Task 2B — Webchat MCP server for structured UI messages
    webchat_token = os.environ.get("NANOBOT_ACCESS_KEY")
    webchat_port = os.environ.get("NANOBOT_WEBCHAT_CONTAINER_PORT", "8765")

    if webchat_token:
        config["tools"]["mcpServers"]["webchat"] = {
            "command": "python",
            "args": ["-m", "mcp_webchat"],
            "env": {
                "WEBCCHAT_ACCESS_TOKEN": webchat_token,
                "WEBCCHAT_PORT": webchat_port,
            },
        }

    # Task 3C — Observability MCP server for logs and traces
    victorialogs_url = os.environ.get("NANOBOT_VICTORIALOGS_URL")
    victoriatraces_url = os.environ.get("NANOBOT_VICTORIATRACES_URL")

    if victorialogs_url or victoriatraces_url:
        config["tools"]["mcpServers"]["observability"] = {
            "command": "python",
            "args": ["-m", "mcp_obs"],
            "env": {},
        }
        if victorialogs_url:
            config["tools"]["mcpServers"]["observability"]["env"][
                "VICTORIALOGS_URL"
            ] = victorialogs_url
        if victoriatraces_url:
            config["tools"]["mcpServers"]["observability"]["env"][
                "VICTORIATRACES_URL"
            ] = victoriatraces_url

    # Write resolved config
    with open(resolved_path, "w") as f:
        json.dump(config, f, indent=2)

    return str(resolved_path)


def main():
    """Resolve config and exec into nanobot gateway."""
    resolved_config = resolve_config()
    workspace = os.environ.get("NANOBOT_WORKSPACE", "/app/nanobot/workspace")

    # Build the command
    cmd = ["nanobot", "gateway", "--config", resolved_config, "--workspace", workspace]

    print(f"Starting nanobot gateway with config: {resolved_config}", file=sys.stderr)
    print(f"Workspace: {workspace}", file=sys.stderr)

    # Exec into nanobot gateway
    os.execvp("nanobot", cmd)


if __name__ == "__main__":
    main()
