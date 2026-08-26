from flask import Blueprint, jsonify, request

from app.models.user import User
from app.schemas.auth import (
    validate_login_payload,
    validate_register_payload,
)
from flask_jwt_extended import get_jwt_identity, jwt_required
from app.services.auth_service import (
    DuplicateEmailError,
    InactiveUserError,
    InvalidCredentialsError,
    authenticate_user,
    register_user,
)
from app.extensions.database import db
from flask_jwt_extended import create_access_token


auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/v1/auth",
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
def register():
    try:
        payload = request.get_json(silent=True)
        data = validate_register_payload(payload)

        user = register_user(
            email=data.email,
            password=data.password,
            first_name=data.first_name,
            last_name=data.last_name,
        )

        return jsonify(
            {
                "success": True,
                "data": _user_response(user),
                "message": "User registered successfully.",
            }
        ), 201

    except ValueError as exc:
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(exc),
                },
            }
        ), 400

    except DuplicateEmailError as exc:
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "EMAIL_ALREADY_EXISTS",
                    "message": str(exc),
                },
            }
        ), 409


@auth_bp.post("/login")
def login():
    try:
        payload = request.get_json(silent=True)
        data = validate_login_payload(payload)

        user = authenticate_user(
            email=data.email,
            password=data.password,
        )

        access_token = create_access_token(
            identity=str(user.id),
        )

        return jsonify(
            {
                "success": True,
                "data": {
                    **_user_response(user),
                    "access_token": access_token,
                },
                "message": "Login successful.",
            }
        ), 200

    except ValueError as exc:
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(exc),
                },
            }
        ), 400

    except (InvalidCredentialsError, InactiveUserError):
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password.",
                },
            }
        ), 401      
        
@auth_bp.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()

    user = db.session.get(User, user_id)

    if user is None:
        return jsonify(
            {
                "success": False,
                "error": {
                    "code": "USER_NOT_FOUND",
                    "message": "User not found.",
                },
            }
        ), 404

    return jsonify(
        {
            "success": True,
            "data": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_active": user.is_active,
            },
            "message": "Authenticated user retrieved successfully.",
        }
    ), 200