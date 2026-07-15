# Project Plugin Dockerfile Template (Airgap Ready)
# Enforces strict transferability without dynamic pip install requirements.
# Guaranteed deterministic via uv.lock synchronization.

FROM ghcr.io/astral-sh/uv:latest AS uv_source
FROM python:3.14-slim as builder

# Copy the uv binary
COPY --from=uv_source /uv /uvx /bin/

WORKDIR /app
RUN apt-get update && apt-get install -y gcc libpq-dev cargo && rm -rf /var/lib/apt/lists/*

# Copy strictly the dependency manifests first for layer caching
COPY pyproject.toml uv.lock ./

# Pre-install dependencies deterministically using the lockfile
# The --frozen flag guarantees CI will fail if uv.lock is out of sync with pyproject.toml
ENV SETUPTOOLS_SCM_PRETEND_VERSION="0.0.0"
RUN uv sync --frozen --no-install-project --no-dev

# Copy the project source
COPY . .

# Final sync to include the project package
RUN uv sync --frozen --no-dev

FROM python:3.14-slim

# CISO Security: Non-root user
RUN apt-get update && apt-get install -y libpq-dev && rm -rf /var/lib/apt/lists/*
RUN useradd -m -s /bin/bash coreason
USER coreason
WORKDIR /home/coreason/project

# Copy the built, deterministic virtual environment from the builder
COPY --from=builder --chown=coreason:coreason /app/.venv /home/coreason/project/.venv

# Copy the Project's True Git Backend workspace
COPY --chown=coreason:coreason . /home/coreason/project

# Prepend the venv to the PATH so python natively uses it
ENV PATH="/home/coreason/project/.venv/bin:$PATH"
ENV PYTHONPATH=/home/coreason/project

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
