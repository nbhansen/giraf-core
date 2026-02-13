"""GIRAF Core — Ninja API root configuration."""
from django.db import connection
from ninja import Schema
from ninja_extra import NinjaExtraAPI
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.controller import NinjaJWTDefaultController

from apps.citizens.api import router as citizens_router
from apps.grades.api import router as grades_router
from apps.invitations.api import org_router as invitations_org_router
from apps.invitations.api import receiver_router as invitations_receiver_router
from apps.organizations.api import router as organizations_router
from apps.pictograms.api import router as pictograms_router
from apps.users.api import router as users_router

api = NinjaExtraAPI(
    title="GIRAF Core API",
    version="1.0.0",
    description="Shared domain service for the GIRAF platform.",
    auth=JWTAuth(),
)


# ---------------------------------------------------------------------------
# Health check (unauthenticated)
# ---------------------------------------------------------------------------


class HealthOut(Schema):
    status: str
    db: str


@api.get("/health", response=HealthOut, auth=None, tags=["health"])
def health(request):
    """Unauthenticated health check with DB connectivity test."""
    try:
        connection.ensure_connection()
        db_status = "ok"
    except Exception:
        db_status = "unavailable"
    return {"status": "ok", "db": db_status}


# Register JWT token endpoints: /api/v1/token/pair, /api/v1/token/refresh, /api/v1/token/verify
api.register_controllers(NinjaJWTDefaultController)

# Register app routers
api.add_router("", users_router)
api.add_router("/organizations", organizations_router)
api.add_router("", citizens_router)
api.add_router("", grades_router)
api.add_router("/pictograms", pictograms_router)
api.add_router("/organizations", invitations_org_router)
api.add_router("/invitations", invitations_receiver_router)
