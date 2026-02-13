"""User API endpoints."""
from django.core.exceptions import ValidationError
from ninja import Router, Schema

from apps.users.schemas import RegisterIn, UserOut
from apps.users.services import UserService

router = Router(tags=["users"])


class ErrorOut(Schema):
    detail: str | list[str]


@router.post("/auth/register", response={201: UserOut, 409: ErrorOut, 422: ErrorOut}, auth=None)
def register(request, payload: RegisterIn):
    """Register a new user account."""
    try:
        user = UserService.register(
            username=payload.username,
            password=payload.password,
            email=payload.email,
            first_name=payload.first_name,
            last_name=payload.last_name,
        )
    except ValueError as e:
        return 409, {"detail": str(e)}
    except ValidationError as e:
        return 422, {"detail": e.messages}
    return 201, user


@router.get("/users/me", response=UserOut)
def me(request):
    """Get the current authenticated user's profile."""
    return request.auth
