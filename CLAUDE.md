# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

GIRAF Core is the shared domain service (Django 5 + Django Ninja + PostgreSQL 16) for the GIRAF platform. Three app backends (Weekplanner, Food Planner, VTA) depend on it for users, organizations, citizens, grades, pictograms, invitations, and JWT authentication.

## Commands

```bash
uv sync --all-extras                      # Install deps
docker compose up -d core-db              # Start PostgreSQL
uv run python manage.py migrate           # Run migrations
uv run python manage.py runserver         # Dev server on :8000

# Tests (SQLite in-memory, config/settings/test.py)
uv run pytest                             # All tests
uv run pytest apps/users/ -v              # Single app
uv run pytest apps/users/tests/test_api.py::test_register -v  # Single test

# Lint & type check
uv run ruff check . && uv run ruff format .
uv run mypy apps/ config/ core/
```

## Architecture

Every Django app follows: `models.py` → `schemas.py` → `services.py` → `api.py`

- **Business logic lives in `services.py`**, never in API endpoints. Endpoints do: auth check → call service → return response.
- **Services raise domain exceptions** (`core/exceptions.py`: `ResourceNotFoundError`, `ConflictError`, `BadRequestError`, `BusinessValidationError`, `ServiceError`) — caught by centralized handlers in `config/api.py`.
- **Permissions**: `core/permissions.py` provides `check_role(user, org_id, min_role)`. Role hierarchy: `owner > admin > member`.
- **JWT**: Custom `TokenObtainPairInputSchema` in `core/jwt.py` embeds `org_roles` claim (`{"1": "owner", "5": "member"}`) so app backends can authorize without calling Core.
- **Router registration**: All routers are added in `config/api.py`. Uses `NinjaExtraAPI` (not plain `NinjaAPI`) — required for JWT controller.
- **Error responses**: Use `ErrorOut` schema (`{"detail": "..."}`) and declare all status codes in the endpoint's `response=` dict.

## Design Philosophy

- **Prefer clarity over clever optimizations.** This platform serves a small number of concurrent users, so always choose clean architecture and readable code over micro-optimizations (e.g. an extra PK lookup to keep service boundaries clean is perfectly fine).

## Key Technical Details

- `AUTH_USER_MODEL = "users.User"` — custom User extending `AbstractUser`
- Settings split: `config/settings/base.py`, `dev.py`, `test.py`, `prod.py`
- Invitations use two routers: `org_router` (admin-scoped at `/organizations`) and `receiver_router` (user-scoped at `/invitations`)
- Pictograms with `organization=None` are global; list uses `Q(org_id=x) | Q(org__isnull=True)`
- Tests auth pattern: `POST /api/v1/token/pair` → extract access token → `HTTP_AUTHORIZATION` header
- Test factories use `factory_boy` in `apps/<name>/tests/factories.py`
- Ruff config: line-length 120, target py312, migrations excluded
