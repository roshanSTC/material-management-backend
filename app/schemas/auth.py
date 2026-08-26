from dataclasses import dataclass


@dataclass(frozen=True)
class RegisterData:
    email: str
    password: str
    first_name: str
    last_name: str


@dataclass(frozen=True)
class LoginData:
    email: str
    password: str


def validate_register_payload(payload: dict) -> RegisterData:
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object.")

    email = payload.get("email")
    password = payload.get("password")
    first_name = payload.get("first_name")
    last_name = payload.get("last_name")

    if not isinstance(email, str) or not email.strip():
        raise ValueError("Email is required.")

    if not isinstance(password, str) or not password:
        raise ValueError("Password is required.")

    if not isinstance(first_name, str) or not first_name.strip():
        raise ValueError("First name is required.")

    if not isinstance(last_name, str) or not last_name.strip():
        raise ValueError("Last name is required.")

    email = email.strip().lower()
    first_name = first_name.strip()
    last_name = last_name.strip()

    if len(email) > 255:
        raise ValueError("Email must not exceed 255 characters.")

    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters.")

    if len(first_name) > 100:
        raise ValueError("First name must not exceed 100 characters.")

    if len(last_name) > 100:
        raise ValueError("Last name must not exceed 100 characters.")

    return RegisterData(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
    )


def validate_login_payload(payload: dict) -> LoginData:
    if not isinstance(payload, dict):
        raise ValueError("Request body must be a JSON object.")

    email = payload.get("email")
    password = payload.get("password")

    if not isinstance(email, str) or not email.strip():
        raise ValueError("Email is required.")

    if not isinstance(password, str) or not password:
        raise ValueError("Password is required.")

    return LoginData(
        email=email.strip().lower(),
        password=password,
    )