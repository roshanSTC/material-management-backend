from flask_smorest import Blueprint
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)

from app.extensions.database import db
from app.models.user import User
from app.schemas.auth import (
    RegisterRequestSchema,
    LoginRequestSchema,
    UserResponseSchema,
    LoginResponseSchema,
    RegisterResponseSchema,
    UpdateProfileRequestSchema,
    ProfileResponseSchema,
    ErrorResponseSchema,
)
from app.services.auth_service import (
    DuplicateEmailError,
    InactiveUserError,
    InvalidCredentialsError,
    UserNotFoundError,
    authenticate_user,
    register_user,
    update_user_profile,
)


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/v1/auth",
    description="Authentication APIs",
)


def _user_response(user):
    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_active": user.is_active,
    }


@auth_bp.post("/register")
@auth_bp.arguments(RegisterRequestSchema)
def register(data):
    try:
        user = register_user(
            email=data["email"],
            password=data["password"],
            first_name=data["first_name"],
            last_name=data["last_name"],
        )

        return {
            "success": True,
            "data": _user_response(user),
            "message": "User registered successfully.",
        }

    except DuplicateEmailError as exc:
        return {
            "success": False,
            "error": {
                "code": "EMAIL_ALREADY_EXISTS",
                "message": str(exc),
            },
        }, 409


@auth_bp.post("/login")
@auth_bp.arguments(LoginRequestSchema)
def login(data):
    try:
        user = authenticate_user(
            email=data["email"],
            password=data["password"],
        )

        access_token = create_access_token(
            identity=str(user.id),
        )
        
        refresh_token = create_refresh_token(
            identity=str(user.id),
        )

        return {
            "success": True,
            "data": {
                **_user_response(user),
                "access_token": access_token,
                "refresh_token": refresh_token,
            },
            "message": "Login successful.",
        }, 200

    except (InvalidCredentialsError, InactiveUserError):
        return {
            "success": False,
            "error": {
                "code": "INVALID_CREDENTIALS",
                "message": "Invalid email or password.",
            },
        }, 401


@auth_bp.put("/profile")
@auth_bp.doc(
    security=[{"BearerAuth": []}],
    summary="Update Profile",
    description="Update the profile (first_name, last_name, email) of the currently authenticated user.",
)
@auth_bp.arguments(UpdateProfileRequestSchema)
@auth_bp.response(200, ProfileResponseSchema)
@jwt_required()
def update_profile(data):
    try:
        user_id = int(get_jwt_identity())
        user = update_user_profile(
            user_id,
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            email=data.get("email"),
        )
        return {
            "success": True,
            "data": _user_response(user),
            "message": "Profile updated successfully.",
        }, 200
    except DuplicateEmailError as exc:
        return {
            "success": False,
            "error": {
                "code": "EMAIL_ALREADY_EXISTS",
                "message": str(exc),
            },
        }, 409
    except (ValueError, TypeError, UserNotFoundError):
        return {
            "success": False,
            "error": {
                "code": "USER_NOT_FOUND",
                "message": "User not found.",
            },
        }, 404
    except Exception as exc:
        return {
            "success": False,
            "error": {
                "code": "PROFILE_UPDATE_FAILED",
                "message": str(exc),
            },
        }, 500


@auth_bp.post("/refresh")
@auth_bp.doc(security=[{"BearerAuth": []}])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()

    user = db.session.get(User, user_id)

    if user is None:
        return {
            "success": False,
            "error": {
                "code": "USER_NOT_FOUND",
                "message": "User not found.",
            },
        }, 404

    if not user.is_active:
        return {
            "success": False,
            "error": {
                "code": "INACTIVE_USER",
                "message": "User account is inactive.",
            },
        }, 403

    access_token = create_access_token(
        identity=str(user.id),
    )

    return {
        "success": True,
        "data": {
            "access_token": access_token,
            "expires_in": 2592000
        },
        "message": "Access token refreshed successfully.",
    }, 200