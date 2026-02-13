"""User API endpoints."""

from django.core.exceptions import ValidationError
from ninja import File, Router, Schema
from ninja.files import UploadedFile

from apps.users.schemas import PasswordChangeIn, RegisterIn, UserOut, UserUpdateIn
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


@router.put("/users/me", response={200: UserOut, 422: ErrorOut})
def update_profile(request, payload: UserUpdateIn):
    """Update current user's profile."""
    updated = UserService.update_user(request.auth, **payload.dict(exclude_unset=True))
    return 200, updated


@router.put("/users/me/password", response={200: UserOut, 400: ErrorOut, 422: ErrorOut})
def change_password(request, payload: PasswordChangeIn):
    """Change user's password."""
    try:
        UserService.change_password(request.auth, payload.old_password, payload.new_password)
    except ValueError as e:
        return 400, {"detail": str(e)}
    except ValidationError as e:
        return 422, {"detail": e.messages}
    return 200, request.auth


@router.delete("/users/me", response={204: None})
def delete_account(request):
    """Delete the current user's account."""
    UserService.delete_user(request.auth)
    return 204, None


@router.post("/users/me/profile-picture", response={200: UserOut, 422: ErrorOut})
def upload_profile_picture(request, file: File[UploadedFile]):
    """Upload a profile picture."""
    try:
        UserService.upload_profile_picture(request.auth, file)
    except ValidationError as e:
        return 422, {"detail": e.messages if hasattr(e, "messages") else str(e)}

    return 200, request.auth
