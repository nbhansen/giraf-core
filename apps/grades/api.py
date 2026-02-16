"""Grade API endpoints."""

from django.shortcuts import get_object_or_404
from ninja import Router
from ninja.errors import HttpError
from ninja.pagination import LimitOffsetPagination, paginate

from apps.grades.models import Grade
from apps.grades.schemas import GradeCitizenAssignIn, GradeCreateIn, GradeOut, GradeUpdateIn
from apps.grades.services import GradeService
from apps.organizations.models import OrgRole
from core.permissions import check_role
from core.schemas import ErrorOut

router = Router(tags=["grades"])


def _check_role_or_raise(user, org_id: int, min_role: str) -> None:
    allowed, msg = check_role(user, org_id, min_role=min_role)
    if not allowed:
        raise HttpError(403, msg)


@router.post(
    "/organizations/{org_id}/grades",
    response={201: GradeOut, 403: ErrorOut},
)
def create_grade(request, org_id: int, payload: GradeCreateIn):
    """Create a grade in an organization. Requires admin role."""
    _check_role_or_raise(request.auth, org_id, OrgRole.ADMIN)
    grade = GradeService.create_grade(name=payload.name, org_id=org_id)
    return 201, grade


@router.get(
    "/organizations/{org_id}/grades",
    response=list[GradeOut],
)
@paginate(LimitOffsetPagination)
def list_grades(request, org_id: int):
    """List grades in an organization. Requires membership."""
    _check_role_or_raise(request.auth, org_id, OrgRole.MEMBER)
    return GradeService.list_grades(org_id)


@router.patch(
    "/grades/{grade_id}",
    response={200: GradeOut, 403: ErrorOut, 404: ErrorOut},
)
def update_grade(request, grade_id: int, payload: GradeUpdateIn):
    """Update a grade. Requires admin role in the grade's org."""
    grade = get_object_or_404(Grade, id=grade_id)
    _check_role_or_raise(request.auth, grade.organization_id, OrgRole.ADMIN)
    updated = GradeService.update_grade(grade, name=payload.name)
    return 200, updated


@router.delete(
    "/grades/{grade_id}",
    response={204: None, 403: ErrorOut, 404: ErrorOut},
)
def delete_grade(request, grade_id: int):
    """Delete a grade. Requires admin role in the grade's org."""
    grade = get_object_or_404(Grade, id=grade_id)
    _check_role_or_raise(request.auth, grade.organization_id, OrgRole.ADMIN)
    GradeService.delete_grade(grade)
    return 204, None


@router.get(
    "/grades/{grade_id}",
    response={200: GradeOut, 403: ErrorOut, 404: ErrorOut},
)
def get_grade(request, grade_id: int):
    """Get a grade by ID. Requires membership in the grade's org."""
    grade = get_object_or_404(Grade, id=grade_id)
    _check_role_or_raise(request.auth, grade.organization_id, OrgRole.MEMBER)
    return 200, grade


@router.post(
    "/grades/{grade_id}/citizens",
    response={200: GradeOut, 400: ErrorOut, 403: ErrorOut, 404: ErrorOut},
)
def assign_citizens(request, grade_id: int, payload: GradeCitizenAssignIn):
    """Assign citizens to a grade (replaces entire set). Requires admin role."""
    grade = get_object_or_404(Grade, id=grade_id)
    _check_role_or_raise(request.auth, grade.organization_id, OrgRole.ADMIN)
    updated = GradeService.assign_citizens(grade, payload.citizen_ids)
    return 200, updated


@router.post(
    "/grades/{grade_id}/citizens/add",
    response={200: GradeOut, 400: ErrorOut, 403: ErrorOut, 404: ErrorOut},
)
def add_citizens_to_grade(request, grade_id: int, payload: GradeCitizenAssignIn):
    """Add citizens to a grade without removing existing ones. Requires admin role."""
    grade = get_object_or_404(Grade, id=grade_id)
    _check_role_or_raise(request.auth, grade.organization_id, OrgRole.ADMIN)
    updated = GradeService.add_citizens(grade, payload.citizen_ids)
    return 200, updated


@router.post(
    "/grades/{grade_id}/citizens/remove",
    response={200: GradeOut, 403: ErrorOut, 404: ErrorOut},
)
def remove_citizens_from_grade(request, grade_id: int, payload: GradeCitizenAssignIn):
    """Remove citizens from a grade. Requires admin role."""
    grade = get_object_or_404(Grade, id=grade_id)
    _check_role_or_raise(request.auth, grade.organization_id, OrgRole.ADMIN)
    updated = GradeService.remove_citizens(grade, payload.citizen_ids)
    return 200, updated
