"""Tests for PictogramService."""

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.pictograms.services import PictogramService
from core.exceptions import BusinessValidationError


def _make_test_image(fmt="PNG", name="test.png") -> SimpleUploadedFile:
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), color="red").save(buf, format=fmt)
    buf.seek(0)
    content_type = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}[fmt]
    return SimpleUploadedFile(name, buf.read(), content_type=content_type)


@pytest.mark.django_db
class TestPictogramServiceUpload:
    def test_upload_invalid_mime_type(self):
        file = SimpleUploadedFile("test.txt", b"not an image", content_type="text/plain")
        with pytest.raises(BusinessValidationError, match="Only JPEG, PNG, and WebP"):
            PictogramService.upload_pictogram(name="Bad", image=file)

    def test_upload_oversized_file(self):
        buf = io.BytesIO()
        Image.new("RGB", (10, 10)).save(buf, format="PNG")
        buf.seek(0)
        file = SimpleUploadedFile("big.png", buf.read() + b"\x00" * (6 * 1024 * 1024), content_type="image/png")
        with pytest.raises(BusinessValidationError, match="5MB"):
            PictogramService.upload_pictogram(name="Big", image=file)

    def test_upload_corrupted_image(self):
        file = SimpleUploadedFile("fake.png", b"not actually an image", content_type="image/png")
        with pytest.raises(BusinessValidationError, match="not a valid image"):
            PictogramService.upload_pictogram(name="Fake", image=file)

    def test_upload_valid_image_succeeds(self):
        image = _make_test_image()
        p = PictogramService.upload_pictogram(name="Valid", image=image)
        assert p.pk is not None
        assert p.name == "Valid"
