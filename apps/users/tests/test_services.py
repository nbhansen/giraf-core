import pytest
from django.test import TestCase

from apps.users.models import User
from apps.users.services import UserService
from core.exceptions import BusinessValidationError, ConflictError


@pytest.mark.django_db
class TestUserService(TestCase):
    def setUp(self):
        self.user = UserService.register(
            username="testuser",
            password="StrongPassword123!",
            email="test@example.com",
            first_name="Test",
            last_name="User",
        )

    def test_register_duplicate_username(self):
        """Test that registering a duplicate username raises ConflictError."""
        with self.assertRaises(ConflictError):
            UserService.register(username="testuser", password="AnotherStrongPassword123!")

    def test_change_password_incorrect_old_password(self):
        """Test that changing password with wrong old password raises BusinessValidationError."""
        with self.assertRaises(BusinessValidationError):
            UserService.change_password(
                user_id=self.user.id, old_password="wrongpassword", new_password="NewStrongPassword123!"
            )

    def test_change_password_weak_new_password(self):
        """Test that changing password to weak password raises BusinessValidationError."""
        with self.assertRaises(BusinessValidationError):
            UserService.change_password(user_id=self.user.id, old_password="StrongPassword123!", new_password="weak")

    def test_delete_user(self):
        """Test deleting a user."""
        user_id = self.user.id
        UserService.delete_user(user_id=self.user.id)
        self.assertFalse(User.objects.filter(id=user_id).exists())
