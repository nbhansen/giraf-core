"""Business logic for user operations.

All business logic lives here — never in API endpoints.
"""

import mimetypes

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction

from apps.users.models import User
from core.exceptions import BusinessValidationError, ConflictError, ResourceNotFoundError


class UserService:
    @staticmethod
    def _get_user_or_raise(user_id: int) -> User:
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ResourceNotFoundError(f"User {user_id} not found.")

    @staticmethod
    @transaction.atomic
    def register(
        *, username: str, password: str, email: str | None = None, first_name: str = "", last_name: str = ""
    ) -> User:
        """Create a new user with validated password.

        Raises:
            ConflictError: If username already exists.
            BusinessValidationError: If password doesn't meet strength requirements.
        """
        if User.objects.filter(username=username).exists():
            raise ConflictError(f"Username '{username}' is already taken.")

        # Validate password strength using Django's validators
        try:
            validate_password(password)
        except DjangoValidationError as e:
            raise BusinessValidationError(e.messages)

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email or "",
            first_name=first_name,
            last_name=last_name,
        )
        return user

    @staticmethod
    @transaction.atomic
    def update_user(
        *, user_id: int, first_name: str | None = None, last_name: str | None = None, email: str | None = None
    ) -> User:
        """Update user profile fields. Only updates non-None values."""
        user = UserService._get_user_or_raise(user_id)
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if email is not None:
            user.email = email
        user.save()
        return user

    @staticmethod
    @transaction.atomic
    def change_password(*, user_id: int, old_password: str, new_password: str) -> User:
        """Change user password with validation.

        Raises:
            BusinessValidationError: If old password is incorrect or new password is weak.
        """
        user = UserService._get_user_or_raise(user_id)
        if not user.check_password(old_password):
            raise BusinessValidationError("Old password is incorrect.")

        # Django's built-in password validators (min length 8, etc.)
        try:
            validate_password(new_password)
        except DjangoValidationError as e:
            raise BusinessValidationError(e.messages)

        user.set_password(new_password)
        user.save()
        return user

    @staticmethod
    @transaction.atomic
    def delete_user(*, user_id: int) -> None:
        """Hard delete user account."""
        user = UserService._get_user_or_raise(user_id)
        user.delete()

    @staticmethod
    @transaction.atomic
    def upload_profile_picture(*, user_id: int, file) -> User:
        """Upload and validate profile picture.

        Raises:
            BusinessValidationError: If file type or size is invalid.
        """
        user = UserService._get_user_or_raise(user_id)

        # Validate file type
        mime_type, _ = mimetypes.guess_type(file.name)
        allowed_types = ["image/jpeg", "image/png", "image/webp"]
        if mime_type not in allowed_types:
            raise BusinessValidationError("Only JPEG, PNG, and WebP images are allowed.")

        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024
        if file.size > max_size:
            raise BusinessValidationError("File size must not exceed 5MB.")

        # Delete old profile picture if exists
        if user.profile_picture:
            user.profile_picture.delete(save=False)

        # Save new profile picture
        user.profile_picture.save(file.name, file, save=True)
        return user
