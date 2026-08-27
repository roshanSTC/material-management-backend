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
    ErrorResponseSchema,
)
from app.services.auth_service import (
    DuplicateEmailError,
    InactiveUserError,
    InvalidCredentialsError,
    authenticate_user,
    register_user,
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


@auth_bp.get("/me")
@auth_bp.doc(security=[{"BearerAuth": []}])
@jwt_required()
def me():
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

    return {
        "success": True,
        "data": _user_response(user),
        "message": "Authenticated user retrieved successfully.",
    }
    

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