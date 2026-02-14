"""Pydantic schemas for the users app."""

from ninja import Schema
from pydantic import EmailStr


class RegisterIn(Schema):
    username: str
    password: str
    email: EmailStr | None = None
    first_name: str = ""
    last_name: str = ""


class UserUpdateIn(Schema):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None


class PasswordChangeIn(Schema):
    old_password: str
    new_password: str


class UserOut(Schema):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    display_name: str
    is_active: bool
    profile_picture: str | None
