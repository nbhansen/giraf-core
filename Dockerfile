FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml .
RUN uv sync --no-dev --no-install-project

COPY . .

EXPOSE 8000

CMD ["uv", "run", "gunicorn", "config.wsgi:application", "-c", "gunicorn.conf.py"]
