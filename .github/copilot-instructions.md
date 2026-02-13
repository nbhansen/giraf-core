# GIRAF Core API — Copilot Instructions

**Human-facing docs (setup, API reference, env vars) live in [README.md](../README.md). Do not duplicate that here.**

## What this repo is
GIRAF Core is the shared domain service for the GIRAF platform. Three app backends (Weekplanner, Food Planner, VTA) depend on it for users, organizations, citizens, grades, pictograms, invitations, and JWT authentication. App backends call Core's REST API for shared data and validate JWTs locally using a shared `JWT_SECRET`.

## Codebase orientation

- `config/api.py` — central router registration (`NinjaExtraAPI`, all `add_router()` calls)
- `config/settings/` — `base.py` (shared), `dev.py`, `test.py`, `prod.py`
- `config/urls.py` — mounts `/admin` + `/api/v1/`
- `apps/<name>/` — each Django app follows the pattern below
- `core/permissions.py` — reusable `check_role()` and `get_membership_or_none()`
- `core/jwt.py` — custom `TokenObtainPairInputSchema` embedding `org_roles` in JWT

### App structure pattern (every app follows this)
```
apps/<name>/
  models.py      # Django models
  schemas.py     # Ninja/Pydantic input/output schemas
  services.py    # Business logic (called by api.py, never the reverse)
  api.py         # Ninja Router with endpoint handlers
  admin.py       # Django admin registration
  tests/
    factories.py # factory_boy factories (if needed)
    test_*.py    # pytest tests
```

## Conventions

### Business logic never in endpoints
API handlers do: auth check → call service → return response. All logic lives in `services.py`.

### Permission checks
```python
from core.permissions import check_role
ok, msg = check_role(request.auth, org_id, min_role=OrgRole.ADMIN)
if not ok:
    return 403, {"detail": msg}
```
Role hierarchy: `owner > admin > member`. `min_role="admin"` passes for admins AND owners.

### Error responses
Always use `ErrorOut` schema (`{"detail": "..."}`) and declare all status codes in the `response=` dict on the endpoint decorator.

### Router registration
New routers go in `config/api.py` — import and `api.add_router(...)`.

### Testing
- **TDD**: write tests first, confirm red, then implement.
- Auth in tests: `POST /api/v1/token/pair` → extract access token → pass as `HTTP_AUTHORIZATION` header.
- Test settings: `config/settings/test.py` (SQLite in-memory, MD5 hasher).
- Factories in `apps/<name>/tests/factories.py` using `factory_boy`.

## Key technical details

- Uses `NinjaExtraAPI` (not plain `NinjaAPI`) — required for JWT controller registration.
- `AUTH_USER_MODEL = "users.User"` — custom User extending `AbstractUser`.
- JWT claim `org_roles` is set on the `RefreshToken` *before* generating the access token (claims propagate). Configured via `TOKEN_OBTAIN_PAIR_INPUT_SCHEMA` in `NINJA_JWT` settings.
- Invitations use two routers: `org_router` (admin-scoped, mounted at `/organizations`) and `receiver_router` (user-scoped, mounted at `/invitations`).
- Pictograms with `organization=None` are global; list endpoint uses `Q(org_id=x) | Q(org__isnull=True)`.
