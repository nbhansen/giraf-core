"""Pydantic schemas for the users app."""
from ninja import Schema


class RegisterIn(Schema):
    username: str
    password: str
    email: str = ""
    first_name: str = ""
    last_name: str = ""


class UserOut(Schema):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    display_name: str
    is_active: bool
