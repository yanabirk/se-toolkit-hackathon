# Nanobot gateway Dockerfile
# Multi-stage build with uv

ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}astral/uv:python3.14-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
ENV UV_NO_DEV=1
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Copy root workspace files (from 'workspace' additional_contexts)
COPY --from=workspace pyproject.toml uv.lock ./

# Copy mcp-lms package (from 'workspace' additional_contexts)
COPY --from=workspace mcp/mcp-lms ./mcp/mcp-lms

# Copy mcp-obs package (from 'workspace' additional_contexts)
COPY --from=workspace mcp/mcp-obs ./mcp/mcp-obs

# Copy nanobot-websocket-channel packages (from 'workspace' additional_contexts)
COPY --from=workspace nanobot-websocket-channel ./nanobot-websocket-channel

# Copy nanobot package files (from build context ./nanobot)
COPY pyproject.toml ./nanobot/pyproject.toml
COPY entrypoint.py ./nanobot/entrypoint.py
COPY config.json ./nanobot/config.json
COPY workspace ./nanobot/workspace/

# Sync only nanobot package (not the entire workspace)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-workspace --package nanobot

# Install mcp-lms (it's a workspace package, need to install separately)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -e /app/mcp/mcp-lms

# Install mcp-obs
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -e /app/mcp/mcp-obs

# Install mcp-webchat and nanobot-webchat
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -e /app/nanobot-websocket-channel/mcp-webchat && \
    uv pip install -e /app/nanobot-websocket-channel/nanobot-webchat

# ---
# Stage 2: Final runtime image
# ---

ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}python:3.14.2-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8

# Accept APP_UID and APP_GID as build args for consistent user IDs
ARG APP_UID=1000
ARG APP_GID=1000

# Create non-root user with specified UID/GID
RUN groupadd --system --gid ${APP_GID} nonroot \
    && useradd --system --gid ${APP_GID} --uid ${APP_UID} --create-home nonroot

# Copy the application from builder
COPY --from=builder --chown=nonroot:nonroot /app /app

# Set proper permissions for workspace directories
RUN chown -R nonroot:nonroot /app/nanobot/workspace && \
    chmod -R 755 /app/nanobot/workspace

# Set PATH to include the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Switch to non-root user
USER nonroot

WORKDIR /app

# Run the entrypoint which resolves config and starts nanobot gateway
CMD ["python", "/app/nanobot/entrypoint.py"]
