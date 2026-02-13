"""Pydantic schemas for organizations."""
from ninja import Schema


class OrgCreateIn(Schema):
    name: str


class OrgOut(Schema):
    id: int
    name: str


class MemberOut(Schema):
    id: int
    user_id: int
    username: str
    role: str

    @staticmethod
    def resolve_username(obj):
        return obj.user.username


class MemberRoleUpdateIn(Schema):
    role: str
