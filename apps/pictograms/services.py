"""Business logic for pictogram operations."""

import mimetypes

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Q
from PIL import Image

from apps.pictograms.models import Pictogram
from core.exceptions import BusinessValidationError, ResourceNotFoundError


class PictogramService:
    @staticmethod
    def _get_pictogram_or_raise(pictogram_id: int) -> Pictogram:
        try:
            return Pictogram.objects.get(id=pictogram_id)
        except Pictogram.DoesNotExist:
            raise ResourceNotFoundError(f"Pictogram {pictogram_id} not found.")

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
    def get_pictogram(pictogram_id: int) -> Pictogram:
        return PictogramService._get_pictogram_or_raise(pictogram_id)

    @staticmethod
    @transaction.atomic
    def upload_pictogram(*, name: str, image, organization_id: int | None = None) -> Pictogram:
        """Upload a pictogram image with validation.

        Raises:
            BusinessValidationError: If file type or size is invalid.
        """
        mime_type, _ = mimetypes.guess_type(image.name)
        allowed_types = ["image/jpeg", "image/png", "image/webp"]
        if mime_type not in allowed_types:
            raise BusinessValidationError("Only JPEG, PNG, and WebP images are allowed.")

        max_size = 5 * 1024 * 1024
        if image.size > max_size:
            raise BusinessValidationError("File size must not exceed 5MB.")

        try:
            Image.open(image).verify()
            image.seek(0)
        except Exception:
            raise BusinessValidationError("File is not a valid image.")

        return Pictogram.objects.create(
            name=name,
            image=image,
            organization_id=organization_id,
        )

    @staticmethod
    @transaction.atomic
    def delete_pictogram(*, pictogram_id: int) -> None:
        pictogram = PictogramService._get_pictogram_or_raise(pictogram_id)
        pictogram.delete()
