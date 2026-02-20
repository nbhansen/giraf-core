"""Tests for OrganizationService error paths."""

import pytest

from apps.organizations.services import OrganizationService
from core.exceptions import ResourceNotFoundError


@pytest.mark.django_db
class TestOrganizationServiceErrors:
    def test_get_organization_not_found(self):
        with pytest.raises(ResourceNotFoundError):
            OrganizationService.get_organization(99999)

    def test_update_organization_not_found(self):
        with pytest.raises(ResourceNotFoundError):
            OrganizationService.update_organization(org_id=99999, name="Ghost")

    def test_delete_organization_not_found(self):
        with pytest.raises(ResourceNotFoundError):
            OrganizationService.delete_organization(org_id=99999)
