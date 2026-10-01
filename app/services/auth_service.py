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


class UserNotFoundError(AuthError):
    """Raised when a user is not found."""


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


def get_user_profile(user_id: int) -> User:
    user = db.session.get(User, user_id)
    if user is None:
        raise UserNotFoundError("User not found.")
    return user


def update_user_profile(
    user_id: int,
    *,
    first_name: str | None = None,
    last_name: str | None = None,
    email: str | None = None,
) -> User:
    user = db.session.get(User, user_id)
    if user is None:
        raise UserNotFoundError("User not found.")

    if email is not None:
        clean_email = email.strip().lower()
        if clean_email != user.email.lower():
            existing = db.session.execute(
                db.select(User).where(User.email == clean_email, User.id != user_id)
            ).scalar_one_or_none()
            if existing is not None:
                raise DuplicateEmailError("An account with this email already exists.")
            user.email = clean_email

    if first_name is not None and first_name.strip():
        user.first_name = first_name.strip()

    if last_name is not None and last_name.strip():
        user.last_name = last_name.strip()

    db.session.commit()
    return user