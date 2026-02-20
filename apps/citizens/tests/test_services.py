"""Tests for CitizenService."""

import pytest

from apps.citizens.services import CitizenService
from core.exceptions import ResourceNotFoundError


@pytest.mark.django_db
class TestCitizenService:
    def test_get_citizen_nonexistent_raises(self):
        with pytest.raises(ResourceNotFoundError, match="Citizen 99999 not found"):
            CitizenService.get_citizen(99999)
