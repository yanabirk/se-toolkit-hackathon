"""Entry point for running mcp_obs as a module: python -m mcp_obs."""

from mcp_obs.server import main

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
