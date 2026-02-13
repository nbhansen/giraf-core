"""Citizen API endpoints."""
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from ninja.errors import HttpError
from ninja.pagination import LimitOffsetPagination, paginate

from apps.citizens.models import Citizen
from apps.citizens.schemas import CitizenCreateIn, CitizenOut, CitizenUpdateIn
from apps.citizens.services import CitizenService
from apps.organizations.models import OrgRole
from core.permissions import check_role

router = Router(tags=["citizens"])


class ErrorOut(Schema):
    detail: str


# --- Org-scoped endpoints ---


@router.post(
    "/organizations/{org_id}/citizens",
    response={201: CitizenOut, 403: ErrorOut},
)
def create_citizen(request, org_id: int, payload: CitizenCreateIn):
    """Create a citizen in an organization. Requires membership."""
    allowed, msg = check_role(request.auth, org_id, min_role=OrgRole.MEMBER)
    if not allowed:
        return 403, {"detail": msg}
    citizen = CitizenService.create_citizen(
        org_id=org_id, first_name=payload.first_name, last_name=payload.last_name
    )
    return 201, citizen


@router.get(
    "/organizations/{org_id}/citizens",
    response=list[CitizenOut],
)
@paginate(LimitOffsetPagination)
def list_citizens(request, org_id: int):
    """List citizens in an organization. Requires membership."""
    allowed, msg = check_role(request.auth, org_id, min_role=OrgRole.MEMBER)
    if not allowed:
        raise HttpError(403, msg)
    return CitizenService.list_citizens(org_id)


# --- Citizen-scoped endpoints ---


@router.get(
    "/citizens/{citizen_id}",
    response={200: CitizenOut, 403: ErrorOut, 404: ErrorOut},
)
def get_citizen(request, citizen_id: int):
    """Get citizen detail. Requires membership in the citizen's org."""
    citizen = get_object_or_404(Citizen, id=citizen_id)
    allowed, msg = check_role(request.auth, citizen.organization_id, min_role=OrgRole.MEMBER)
    if not allowed:
        return 403, {"detail": msg}
    return 200, citizen


@router.patch(
    "/citizens/{citizen_id}",
    response={200: CitizenOut, 403: ErrorOut, 404: ErrorOut},
)
def update_citizen(request, citizen_id: int, payload: CitizenUpdateIn):
    """Update a citizen. Requires membership in the citizen's org."""
    citizen = get_object_or_404(Citizen, id=citizen_id)
    allowed, msg = check_role(request.auth, citizen.organization_id, min_role=OrgRole.MEMBER)
    if not allowed:
        return 403, {"detail": msg}
    updated = CitizenService.update_citizen(
        citizen, first_name=payload.first_name, last_name=payload.last_name
    )
    return 200, updated


@router.delete(
    "/citizens/{citizen_id}",
    response={204: None, 403: ErrorOut, 404: ErrorOut},
)
def delete_citizen(request, citizen_id: int):
    """Delete a citizen. Requires admin role in the citizen's org."""
    citizen = get_object_or_404(Citizen, id=citizen_id)
    allowed, msg = check_role(request.auth, citizen.organization_id, min_role=OrgRole.ADMIN)
    if not allowed:
        return 403, {"detail": msg}
    CitizenService.delete_citizen(citizen)
    return 204, None
