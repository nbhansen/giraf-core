"""Business logic for pictogram operations."""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Q

from apps.pictograms.models import Pictogram
from core.exceptions import BusinessValidationError


class PictogramService:
    @staticmethod
    @transaction.atomic
    def create_pictogram(*, name: str, image_url: str, organization_id: int | None = None) -> Pictogram:
        try:
            return Pictogram.objects.create(
                name=name,
                image_url=image_url,
                organization_id=organization_id,
            )
        except DjangoValidationError as e:
            raise BusinessValidationError(" ".join(e.messages))

    @staticmethod
    def list_pictograms(organization_id: int | None = None):
        if organization_id:
            return Pictogram.objects.filter(Q(organization_id=organization_id) | Q(organization__isnull=True))
        return Pictogram.objects.filter(organization__isnull=True)

    @staticmethod
    @transaction.atomic
    def upload_pictogram(*, name: str, image, organization_id: int | None = None) -> Pictogram:
        return Pictogram.objects.create(
            name=name,
            image=image,
            organization_id=organization_id,
        )

    @staticmethod
    @transaction.atomic
    def delete_pictogram(pictogram: Pictogram) -> None:
        pictogram.delete()
