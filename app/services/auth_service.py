from app.extensions.database import db
from app.models import User
from app.utils.security import hash_password, verify_password


class AuthError(Exception):
    """Base authentication error."""


class DuplicateEmailError(AuthError):
    """Raised when an email is already registered."""


class InvalidCredentialsError(AuthError):
    """Raised when login credentials are invalid."""


class InactiveUserError(AuthError):
    """Raised when an inactive user attempts to authenticate."""


def register_user(
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
) -> User:
    existing_user = db.session.execute(
        db.select(User).where(User.email == email)
    ).scalar_one_or_none()

    if existing_user is not None:
        raise DuplicateEmailError("An account with this email already exists.")

    user = User(
        email=email,
        password_hash=hash_password(password),
        first_name=first_name,
        last_name=last_name,
        is_active=True,
    )

    db.session.add(user)
    db.session.commit()

    return user


def authenticate_user(*, email: str, password: str) -> User:
    user = db.session.execute(
        db.select(User).where(User.email == email)
    ).scalar_one_or_none()

    if user is None:
        raise InvalidCredentialsError("Invalid email or password.")

    if not user.is_active:
        raise InactiveUserError("User account is inactive.")

    if not verify_password(user.password_hash, password):
        raise InvalidCredentialsError("Invalid email or password.")

    return user