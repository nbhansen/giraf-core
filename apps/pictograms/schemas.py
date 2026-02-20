"""Pictogram schemas."""

from ninja import Schema


class PictogramCreateIn(Schema):
    name: str
    image_url: str
    organization_id: int | None = None


class PictogramOut(Schema):
    id: int
    name: str
    image_url: str
    organization_id: int | None

    @staticmethod
    def resolve_image_url(obj):
        """Return image file URL if uploaded, otherwise the stored image_url."""
        if obj.image:
            return obj.image.url
        return obj.image_url
