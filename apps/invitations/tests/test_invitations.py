"""Tests for Invitation model and API endpoints.

Invitations let org admins invite users to join an organization.
Written BEFORE implementation (TDD red phase).
"""
import pytest
from django.test import Client

from apps.organizations.models import Membership, Organization, OrgRole
from apps.users.tests.factories import UserFactory


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def admin(db):
    return UserFactory(username="admin", password="testpass123")


@pytest.fixture
def receiver(db):
    return UserFactory(
        username="receiver",
        email="receiver@example.com",
        password="testpass123",
    )


@pytest.fixture
def member(db):
    return UserFactory(username="member", password="testpass123")


@pytest.fixture
def outsider(db):
    return UserFactory(username="outsider", password="testpass123")


@pytest.fixture
def org(db, admin, member):
    org = Organization.objects.create(name="Sunflower School")
    Membership.objects.create(user=admin, organization=org, role=OrgRole.ADMIN)
    Membership.objects.create(user=member, organization=org, role=OrgRole.MEMBER)
    return org


def auth_header(client, username, password="testpass123"):
    resp = client.post(
        "/api/v1/token/pair",
        data={"username": username, "password": password},
        content_type="application/json",
    )
    return {"HTTP_AUTHORIZATION": f"Bearer {resp.json()['access']}"}


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInvitationModel:
    def test_create_invitation(self, admin, receiver, org):
        from apps.invitations.models import Invitation, InvitationStatus

        inv = Invitation.objects.create(
            organization=org,
            sender=admin,
            receiver=receiver,
        )
        assert inv.pk is not None
        assert inv.status == InvitationStatus.PENDING
        assert inv.organization == org
        assert inv.sender == admin
        assert inv.receiver == receiver
        assert str(inv) == "Invitation → receiver to Sunflower School (pending)"

    def test_unique_pending_per_user_org(self, admin, receiver, org):
        """Cannot create two pending invitations for the same user+org."""
        from django.db import IntegrityError

        from apps.invitations.models import Invitation

        Invitation.objects.create(
            organization=org, sender=admin, receiver=receiver
        )
        with pytest.raises(IntegrityError):
            Invitation.objects.create(
                organization=org, sender=admin, receiver=receiver
            )

    def test_cascade_delete_org_deletes_invitations(self, admin, receiver, org):
        from apps.invitations.models import Invitation

        Invitation.objects.create(
            organization=org, sender=admin, receiver=receiver
        )
        org.delete()
        assert Invitation.objects.count() == 0


# ---------------------------------------------------------------------------
# API tests — Send invitation
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSendInvitation:
    def test_admin_can_send_invitation(self, client, org, admin, receiver):
        headers = auth_header(client, "admin")
        response = client.post(
            f"/api/v1/organizations/{org.id}/invitations",
            data={"receiver_email": "receiver@example.com"},
            content_type="application/json",
            **headers,
        )
        assert response.status_code == 201
        body = response.json()
        assert body["receiver_username"] == "receiver"
        assert body["organization_name"] == "Sunflower School"
        assert body["status"] == "pending"

    def test_member_cannot_send_invitation(self, client, org, member, receiver):
        headers = auth_header(client, "member")
        response = client.post(
            f"/api/v1/organizations/{org.id}/invitations",
            data={"receiver_email": "receiver@example.com"},
            content_type="application/json",
            **headers,
        )
        assert response.status_code == 403

    def test_cannot_invite_nonexistent_email(self, client, org, admin):
        headers = auth_header(client, "admin")
        response = client.post(
            f"/api/v1/organizations/{org.id}/invitations",
            data={"receiver_email": "nobody@example.com"},
            content_type="application/json",
            **headers,
        )
        assert response.status_code == 404

    def test_cannot_invite_existing_member(self, client, org, admin, member):
        headers = auth_header(client, "admin")
        response = client.post(
            f"/api/v1/organizations/{org.id}/invitations",
            data={"receiver_email": member.email},
            content_type="application/json",
            **headers,
        )
        assert response.status_code == 409

    def test_duplicate_pending_invitation_rejected(
        self, client, org, admin, receiver
    ):
        headers = auth_header(client, "admin")
        # First invite succeeds
        client.post(
            f"/api/v1/organizations/{org.id}/invitations",
            data={"receiver_email": "receiver@example.com"},
            content_type="application/json",
            **headers,
        )
        # Second invite fails
        response = client.post(
            f"/api/v1/organizations/{org.id}/invitations",
            data={"receiver_email": "receiver@example.com"},
            content_type="application/json",
            **headers,
        )
        assert response.status_code == 409


# ---------------------------------------------------------------------------
# API tests — List & respond
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestInvitationFlow:
    def test_receiver_sees_their_invitations(self, client, org, admin, receiver):
        from apps.invitations.models import Invitation

        Invitation.objects.create(
            organization=org, sender=admin, receiver=receiver
        )
        headers = auth_header(client, "receiver")
        response = client.get("/api/v1/invitations/received", **headers)
        assert response.status_code == 200
        body = response.json()["items"]
        assert len(body) == 1
        assert body[0]["organization_name"] == "Sunflower School"

    def test_admin_sees_org_invitations(self, client, org, admin, receiver):
        from apps.invitations.models import Invitation

        Invitation.objects.create(
            organization=org, sender=admin, receiver=receiver
        )
        headers = auth_header(client, "admin")
        response = client.get(
            f"/api/v1/organizations/{org.id}/invitations", **headers
        )
        assert response.status_code == 200
        body = response.json()["items"]
        assert len(body) == 1

    def test_accept_invitation_creates_membership(
        self, client, org, admin, receiver
    ):
        from apps.invitations.models import Invitation, InvitationStatus

        inv = Invitation.objects.create(
            organization=org, sender=admin, receiver=receiver
        )
        headers = auth_header(client, "receiver")
        response = client.post(
            f"/api/v1/invitations/{inv.id}/accept",
            content_type="application/json",
            **headers,
        )
        assert response.status_code == 200
        # Check membership created
        assert Membership.objects.filter(
            user=receiver, organization=org, role=OrgRole.MEMBER
        ).exists()
        # Check invitation status updated
        inv.refresh_from_db()
        assert inv.status == InvitationStatus.ACCEPTED

    def test_reject_invitation(self, client, org, admin, receiver):
        from apps.invitations.models import Invitation, InvitationStatus

        inv = Invitation.objects.create(
            organization=org, sender=admin, receiver=receiver
        )
        headers = auth_header(client, "receiver")
        response = client.post(
            f"/api/v1/invitations/{inv.id}/reject",
            content_type="application/json",
            **headers,
        )
        assert response.status_code == 200
        inv.refresh_from_db()
        assert inv.status == InvitationStatus.REJECTED

    def test_only_receiver_can_respond(self, client, org, admin, receiver):
        from apps.invitations.models import Invitation

        inv = Invitation.objects.create(
            organization=org, sender=admin, receiver=receiver
        )
        headers = auth_header(client, "admin")
        response = client.post(
            f"/api/v1/invitations/{inv.id}/accept",
            content_type="application/json",
            **headers,
        )
        assert response.status_code == 403

    def test_admin_can_delete_org_invitation(self, client, org, admin, receiver):
        from apps.invitations.models import Invitation

        inv = Invitation.objects.create(
            organization=org, sender=admin, receiver=receiver
        )
        headers = auth_header(client, "admin")
        response = client.delete(
            f"/api/v1/organizations/{org.id}/invitations/{inv.id}",
            **headers,
        )
        assert response.status_code == 204
        assert not Invitation.objects.filter(id=inv.id).exists()
