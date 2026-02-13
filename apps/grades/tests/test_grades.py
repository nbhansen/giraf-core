"""Tests for Grade model and API endpoints.

Grades are class groupings of citizens within an organization.
Written BEFORE implementation.
"""
import pytest
from django.test import Client

from apps.citizens.models import Citizen
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
class TestGradeModel:
    def test_create_grade(self):
        from apps.grades.models import Grade

        org = Organization.objects.create(name="Test School")
        grade = Grade.objects.create(name="Class 3A", organization=org)
        assert grade.pk is not None
        assert str(grade) == "Class 3A"

    def test_grade_citizens_m2m(self):
        from apps.grades.models import Grade

        org = Organization.objects.create(name="Test School")
        grade = Grade.objects.create(name="Class 3A", organization=org)
        c1 = Citizen.objects.create(first_name="Alice", last_name="A", organization=org)
        c2 = Citizen.objects.create(first_name="Bob", last_name="B", organization=org)
        grade.citizens.add(c1, c2)
        assert grade.citizens.count() == 2

    def test_cascade_delete_org_deletes_grades(self):
        from apps.grades.models import Grade

        org = Organization.objects.create(name="Test School")
        Grade.objects.create(name="Class 3A", organization=org)
        org.delete()
        assert Grade.objects.count() == 0


@pytest.mark.django_db
class TestGradeAPI:
    def test_create_grade(self, client, org, owner):
        headers = auth_header(client, "owner")
        response = client.post(
            f"/api/v1/organizations/{org.id}/grades",
            data={"name": "Class 3A"},
            content_type="application/json",
            **headers,
        )
        assert response.status_code == 201
        assert response.json()["name"] == "Class 3A"

    def test_non_member_cannot_create_grade(self, client, org, non_member):
        headers = auth_header(client, "outsider")
        response = client.post(
            f"/api/v1/organizations/{org.id}/grades",
            data={"name": "Class 3A"},
            content_type="application/json",
            **headers,
        )
        assert response.status_code == 403

    def test_list_grades(self, client, org, member):
        from apps.grades.models import Grade

        Grade.objects.create(name="Class 3A", organization=org)
        Grade.objects.create(name="Class 3B", organization=org)

        headers = auth_header(client, "member")
        response = client.get(f"/api/v1/organizations/{org.id}/grades", **headers)
        assert response.status_code == 200
        assert len(response.json()["items"]) == 2

    def test_update_grade(self, client, org, owner):
        from apps.grades.models import Grade

        grade = Grade.objects.create(name="Class 3A", organization=org)
        headers = auth_header(client, "owner")
        response = client.patch(
            f"/api/v1/grades/{grade.id}",
            data={"name": "Class 4A"},
            content_type="application/json",
            **headers,
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Class 4A"

    def test_delete_grade(self, client, org, owner):
        from apps.grades.models import Grade

        grade = Grade.objects.create(name="Class 3A", organization=org)
        headers = auth_header(client, "owner")
        response = client.delete(f"/api/v1/grades/{grade.id}", **headers)
        assert response.status_code == 204

    def test_assign_citizens_to_grade(self, client, org, owner):
        from apps.grades.models import Grade

        grade = Grade.objects.create(name="Class 3A", organization=org)
        c1 = Citizen.objects.create(first_name="Alice", last_name="A", organization=org)
        c2 = Citizen.objects.create(first_name="Bob", last_name="B", organization=org)

        headers = auth_header(client, "owner")
        response = client.post(
            f"/api/v1/grades/{grade.id}/citizens",
            data={"citizen_ids": [c1.id, c2.id]},
            content_type="application/json",
            **headers,
        )
        assert response.status_code == 200
        grade.refresh_from_db()
        assert grade.citizens.count() == 2

    def test_member_cannot_delete_grade(self, client, org, member):
        from apps.grades.models import Grade

        grade = Grade.objects.create(name="Class 3A", organization=org)
        headers = auth_header(client, "member")
        response = client.delete(f"/api/v1/grades/{grade.id}", **headers)
        assert response.status_code == 403
