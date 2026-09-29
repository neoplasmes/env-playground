# syntax=docker/dockerfile:1.7
FROM ghcr.io/astral-sh/uv:0.12.20 AS uv
FROM python:3.14.7-slim AS build
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /workspace/python
COPY python/pyproject.toml python/uv.lock ./
COPY python/apps/image_processor/pyproject.toml apps/image_processor/pyproject.toml
COPY python/packages/repo_style/pyproject.toml packages/repo_style/pyproject.toml
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev --no-install-workspace --package image-processor
COPY python/apps/image_processor/src apps/image_processor/src
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev --package image-processor --no-editable

FROM python:3.14.7-slim
RUN groupadd -g 10001 app && useradd -u 10001 -g app app
COPY --from=build /workspace/python/.venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER 10001:10001
EXPOSE 8081
CMD ["python", "-m", "uvicorn", "image_processor.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8081", "--limit-concurrency", "4"]
