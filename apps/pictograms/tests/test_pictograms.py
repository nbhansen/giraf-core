"""Tests for Pictogram model and API endpoints.

Pictograms are visual aids used across all GIRAF apps.
They can be org-specific or global (null organization).
Written BEFORE implementation.
"""
import pytest
from django.test import Client

from apps.organizations.models import Membership, Organization, OrgRole
from apps.users.tests.factories import UserFactory


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def owner(db):
    return UserFactory(username="owner", password="testpass123")


@pytest.fixture
def member(db):
    return UserFactory(username="member", password="testpass123")


@pytest.fixture
def non_member(db):
    return UserFactory(username="outsider", password="testpass123")


@pytest.fixture
def org(db, owner, member):
    org = Organization.objects.create(name="Sunflower School")
    Membership.objects.create(user=owner, organization=org, role=OrgRole.OWNER)
    Membership.objects.create(user=member, organization=org, role=OrgRole.MEMBER)
    return org


def auth_header(client, username, password="testpass123"):
    resp = client.post(
        "/api/v1/token/pair",
        data={"username": username, "password": password},
        content_type="application/json",
    )
    return {"HTTP_AUTHORIZATION": f"Bearer {resp.json()['access']}"}


@pytest.mark.django_db
class TestPictogramModel:
    def test_create_org_pictogram(self):
        from apps.pictograms.models import Pictogram

        org = Organization.objects.create(name="Test School")
        p = Pictogram.objects.create(
            name="Happy Face",
            image_url="https://example.com/happy.png",
            organization=org,
        )
        assert p.pk is not None
        assert p.organization == org
        assert str(p) == "Happy Face"

    def test_create_global_pictogram(self):
        from apps.pictograms.models import Pictogram

        p = Pictogram.objects.create(
            name="Sad Face",
            image_url="https://example.com/sad.png",
            organization=None,
        )
        assert p.pk is not None
        assert p.organization is None


@pytest.mark.django_db
class TestPictogramAPI:
    def test_create_pictogram_for_org(self, client, org, owner):
        headers = auth_header(client, "owner")
        response = client.post(
            "/api/v1/pictograms",
            data={
                "name": "Happy Face",
                "image_url": "https://example.com/happy.png",
                "organization_id": org.id,
            },
            content_type="application/json",
            **headers,
        )
        assert response.status_code == 201
        assert response.json()["name"] == "Happy Face"

    def test_list_pictograms_includes_global_and_org(self, client, org, member):
        from apps.pictograms.models import Pictogram

        Pictogram.objects.create(name="Global", image_url="https://g.com/g.png", organization=None)
        Pictogram.objects.create(name="Org Specific", image_url="https://o.com/o.png", organization=org)

        headers = auth_header(client, "member")
        response = client.get(f"/api/v1/pictograms?organization_id={org.id}", **headers)
        assert response.status_code == 200
        names = [p["name"] for p in response.json()["items"]]
        assert "Global" in names
        assert "Org Specific" in names

    def test_get_pictogram(self, client, org, member):
        from apps.pictograms.models import Pictogram

        p = Pictogram.objects.create(name="Happy", image_url="https://h.com/h.png", organization=org)

        headers = auth_header(client, "member")
        response = client.get(f"/api/v1/pictograms/{p.id}", **headers)
        assert response.status_code == 200

    def test_delete_pictogram(self, client, org, owner):
        from apps.pictograms.models import Pictogram

        p = Pictogram.objects.create(name="Happy", image_url="https://h.com/h.png", organization=org)

        headers = auth_header(client, "owner")
        response = client.delete(f"/api/v1/pictograms/{p.id}", **headers)
        assert response.status_code == 204
        assert not Pictogram.objects.filter(id=p.id).exists()
