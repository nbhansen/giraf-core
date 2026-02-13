# GIRAF Core API

Shared domain service for the GIRAF platform — manages users, organizations, citizens, grades, pictograms, invitations, and authentication.

All GIRAF apps (Weekplanner, Food Planner, Visual Tangible Artefacts) authenticate against and query this service for shared domain data.

## Platform Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Mobile Apps (Expo / React Native)            │
│   Weekplanner          Food Planner          VTA               │
└──────┬──────────────────────┬───────────────────┬──────────────┘
       │ domain data          │ domain data       │ domain data
       ▼                      ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Weekplanner  │   │ Food Planner │   │ VTA Backend  │
│ Backend      │   │ Backend      │   │              │
│ (.NET / C#)  │   │ (TBD)        │   │ (TBD)        │
│ Activities,  │   │ Meals, Menus │   │ Exercises,   │
│ Schedules    │   │ Nutrition    │   │ Progress     │
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       │                  │                   │
       │  users, orgs, citizens, pictograms   │
       ▼                  ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GIRAF Core API  ← (this repo)               │
│                    (Django + Ninja, Python)                     │
│                                                                 │
│  Auth/JWT │ Users │ Orgs │ Citizens │ Grades │ Pictos │ Invites │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                    ┌─────▼─────┐
                    │  Core DB  │
                    │ PostgreSQL│
                    └───────────┘
```

- **Apps authenticate directly with Core** — mobile apps call `/token/pair` to get JWTs
- **JWTs contain `org_roles`** — e.g. `{"1": "owner", "5": "member"}`, so app backends can authorize locally
- **App backends call Core for shared data** — citizens, orgs, grades, pictograms
- **Each app stores only its own domain data** — activities, meals, exercises in separate DBs
- **Core is the single source of truth** — one user account, one org, one citizen record across all apps

## Quick Start

```bash
# Install dependencies
uv sync --all-extras

# Start database
docker compose up -d core-db

# Run migrations
uv run python manage.py migrate

# Create superuser (for Django Admin)
uv run python manage.py createsuperuser

# Run dev server
uv run python manage.py runserver

# Run tests
uv run pytest
```

Or run everything via Docker Compose:

```bash
docker compose up
# API at http://localhost:8000
# Admin at http://localhost:8000/admin
```

## Architecture

- **Django 5.x** with **Django Ninja** API layer
- **PostgreSQL 16** database
- **JWT authentication** via django-ninja-jwt (access: 1h, refresh: 7d)
- Business logic in `services.py`, never in API endpoints
- Each Django app follows: `models.py` → `schemas.py` → `services.py` → `api.py`
- Role hierarchy: **owner > admin > member**

## Interactive API Docs

When running locally: http://localhost:8000/api/v1/docs

## Project Structure

```
config/
  settings/          # base, dev, test, prod
  api.py             # Central router registration
  urls.py            # URL config (admin + API)
apps/
  users/             # Custom user model + registration
  organizations/     # Orgs, membership, roles
  citizens/          # Citizens (the kids)
  grades/            # Grade groupings
  pictograms/        # Visual aids library
  invitations/       # Org invitations
core/
  permissions.py     # Reusable role checks
  jwt.py             # Custom JWT claims (org_roles)
```

---

## API Reference

All endpoints are prefixed with `/api/v1`. Unless noted otherwise, all endpoints require a valid JWT Bearer token.

### Authentication

| Method | Endpoint         | Auth | Description                             |
| ------ | ---------------- | ---- | --------------------------------------- |
| `POST` | `/auth/register` | None | Register a new user                     |
| `POST` | `/token/pair`    | None | Login — returns access + refresh tokens |
| `POST` | `/token/refresh` | None | Refresh an expired access token         |
| `POST` | `/token/verify`  | None | Verify a token is valid                 |
| `GET`  | `/users/me`      | JWT  | Get current user profile                |

#### Register

```
POST /api/v1/auth/register
```

```json
{
  "username": "alice",
  "password": "Str0ngPass!",
  "email": "alice@example.com",
  "first_name": "Alice",
  "last_name": "Smith"
}
```

Returns `201` with user data. `409` if username taken, `422` if password too weak.

#### Login

```
POST /api/v1/token/pair
```

```json
{ "username": "alice", "password": "Str0ngPass!" }
```

Returns:

```json
{
  "access": "eyJ...",
  "refresh": "eyJ...",
  "org_roles": {
    "1": "owner",
    "5": "admin",
    "12": "member"
  }
}
```

The `org_roles` claim is also embedded inside the JWT access token payload itself, so app backends can decode the token to determine user roles without calling the Core API.

---

### Organizations

| Method   | Endpoint                                    | Min Role | Description                        |
| -------- | ------------------------------------------- | -------- | ---------------------------------- |
| `POST`   | `/organizations`                            | JWT      | Create org (creator becomes owner) |
| `GET`    | `/organizations`                            | JWT      | List user's organizations          |
| `GET`    | `/organizations/{org_id}`                   | member   | Get org detail                     |
| `GET`    | `/organizations/{org_id}/members`           | member   | List members                       |
| `PATCH`  | `/organizations/{org_id}/members/{user_id}` | owner    | Update member role                 |
| `DELETE` | `/organizations/{org_id}/members/{user_id}` | admin    | Remove member                      |

---

### Citizens

Citizens are kids with autism, belonging to an organization.

| Method   | Endpoint                           | Min Role | Description          |
| -------- | ---------------------------------- | -------- | -------------------- |
| `POST`   | `/organizations/{org_id}/citizens` | member   | Create citizen       |
| `GET`    | `/organizations/{org_id}/citizens` | member   | List citizens in org |
| `GET`    | `/citizens/{citizen_id}`           | member   | Get citizen detail   |
| `PATCH`  | `/citizens/{citizen_id}`           | member   | Update citizen       |
| `DELETE` | `/citizens/{citizen_id}`           | admin    | Delete citizen       |

---

### Grades

Grades group citizens within an organization.

| Method   | Endpoint                         | Min Role | Description              |
| -------- | -------------------------------- | -------- | ------------------------ |
| `POST`   | `/organizations/{org_id}/grades` | admin    | Create grade             |
| `GET`    | `/organizations/{org_id}/grades` | member   | List grades in org       |
| `PATCH`  | `/grades/{grade_id}`             | admin    | Update grade             |
| `DELETE` | `/grades/{grade_id}`             | admin    | Delete grade             |
| `POST`   | `/grades/{grade_id}/citizens`    | admin    | Assign citizens to grade |

---

### Pictograms

Visual aids used across the platform. Pictograms can be **global** (no org) or **org-specific**.

| Method   | Endpoint                           | Min Role              | Description                                 |
| -------- | ---------------------------------- | --------------------- | ------------------------------------------- |
| `POST`   | `/pictograms`                      | admin (if org-scoped) | Create pictogram                            |
| `GET`    | `/pictograms?organization_id={id}` | JWT                   | List pictograms (global + org if specified) |
| `GET`    | `/pictograms/{pictogram_id}`       | JWT                   | Get pictogram                               |
| `DELETE` | `/pictograms/{pictogram_id}`       | admin (if org-scoped) | Delete pictogram                            |

---

### Invitations

Invitations let org admins invite users by email.

| Method   | Endpoint                                   | Min Role       | Description                         |
| -------- | ------------------------------------------ | -------------- | ----------------------------------- |
| `POST`   | `/organizations/{org_id}/invitations`      | admin          | Send invitation (by receiver email) |
| `GET`    | `/organizations/{org_id}/invitations`      | admin          | List pending invitations for org    |
| `DELETE` | `/organizations/{org_id}/invitations/{id}` | admin          | Revoke/delete invitation            |
| `GET`    | `/invitations/received`                    | JWT (receiver) | List my pending invitations         |
| `POST`   | `/invitations/{id}/accept`                 | JWT (receiver) | Accept — creates membership         |
| `POST`   | `/invitations/{id}/reject`                 | JWT (receiver) | Reject invitation                   |

Guards:

- Cannot invite a user who is already a member → `409`
- Cannot create duplicate pending invitation → `409`
- Cannot invite a nonexistent email → `404`
- Only the receiver can accept/reject → `403`

---

## Role System

Roles are per-organization via the `Membership` model:

| Role       | Can do                                                   |
| ---------- | -------------------------------------------------------- |
| **member** | Read org data, manage citizens                           |
| **admin**  | + invite users, manage grades/pictograms, remove members |
| **owner**  | + change member roles                                    |

Roles follow a hierarchy: `owner > admin > member`. A check for `min_role=admin` passes for both admins and owners.

## Environment Variables

| Variable                 | Default               | Description                     |
| ------------------------ | --------------------- | ------------------------------- |
| `DJANGO_SETTINGS_MODULE` | `config.settings.dev` | Settings module                 |
| `DJANGO_SECRET_KEY`      | `insecure-dev-key...` | Django secret key               |
| `JWT_SECRET`             | Same as `SECRET_KEY`  | JWT signing key                 |
| `POSTGRES_DB`            | `giraf_core`          | Database name                   |
| `POSTGRES_USER`          | `giraf`               | Database user                   |
| `POSTGRES_PASSWORD`      | `giraf`               | Database password               |
| `POSTGRES_HOST`          | `localhost`           | Database host                   |
| `POSTGRES_PORT`          | `5432`                | Database port                   |
| `CORS_ALLOWED_ORIGINS`   | (empty)               | Comma-separated allowed origins |

## Testing

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run a specific app's tests
uv run pytest apps/users/ -v
uv run pytest apps/organizations/ -v

# Run with coverage
uv run pytest --cov=apps --cov=core
```

Tests use SQLite in-memory for speed (configured in `config/settings/test.py`).
