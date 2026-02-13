"""Business logic for user operations.

All business logic lives here — never in API endpoints.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()


class UserService:
    @staticmethod
    def register(*, username: str, password: str, email: str = "", first_name: str = "", last_name: str = "") -> User:
        """Create a new user with validated password.

        Raises:
            ValueError: If username already exists.
            ValidationError: If password doesn't meet strength requirements.
        """
        if User.objects.filter(username=username).exists():
            raise ValueError(f"Username '{username}' is already taken.")

        # Validate password strength using Django's validators
        try:
            validate_password(password)
        except ValidationError:
            raise

        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        return user
