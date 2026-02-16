"""Business logic for grade operations."""

from django.db import transaction

from apps.citizens.models import Citizen
from apps.grades.models import Grade
from core.exceptions import BadRequestError


class GradeService:
    @staticmethod
    def _validate_citizens_belong_to_org(citizen_ids: list[int], org_id: int) -> None:
        """Verify all citizen IDs belong to the given organization."""
        valid = set(Citizen.objects.filter(id__in=citizen_ids, organization_id=org_id).values_list("id", flat=True))
        invalid = set(citizen_ids) - valid
        if invalid:
            raise BadRequestError(f"Citizens do not belong to this organization: {sorted(invalid)}")

    @staticmethod
    @transaction.atomic
    def create_grade(*, name: str, org_id: int) -> Grade:
        return Grade.objects.create(name=name, organization_id=org_id)

    @staticmethod
    def list_grades(org_id: int):
        return Grade.objects.filter(organization_id=org_id)

    @staticmethod
    @transaction.atomic
    def update_grade(grade: Grade, name: str | None) -> Grade:
        if name is not None:
            grade.name = name
            grade.save(update_fields=["name"])
        return grade

    @staticmethod
    @transaction.atomic
    def delete_grade(grade: Grade) -> None:
        grade.delete()

    @staticmethod
    @transaction.atomic
    def assign_citizens(grade: Grade, citizen_ids: list[int]) -> Grade:
        GradeService._validate_citizens_belong_to_org(citizen_ids, grade.organization_id)
        grade.citizens.set(citizen_ids)
        return grade

    @staticmethod
    @transaction.atomic
    def add_citizens(grade: Grade, citizen_ids: list[int]) -> Grade:
        GradeService._validate_citizens_belong_to_org(citizen_ids, grade.organization_id)
        grade.citizens.add(*citizen_ids)
        return grade

    @staticmethod
    @transaction.atomic
    def remove_citizens(grade: Grade, citizen_ids: list[int]) -> Grade:
        grade.citizens.remove(*citizen_ids)
        return grade
