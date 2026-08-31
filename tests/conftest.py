
import os
import sys
from pathlib import Path

import pytest
from flask_jwt_extended import create_access_token

# Add project root to Python import path.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.extensions.database import db
from app.models import Customer, Project, Supplier, User
from app.config.settings import Config


class TestConfig(Config):
    TESTING = True

    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        "test-jwt-secret-key",
    )

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/material_management_test",
    )


@pytest.fixture
def app():
    app = create_app(TestConfig)

    with app.app_context():
        db.drop_all()
        db.create_all()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def test_user(app):
    user = User(
        email="test@example.com",
        password_hash="test-password-hash",
        first_name="Test",
        last_name="User",
        is_active=True,
    )

    db.session.add(user)
    db.session.commit()

    return user


@pytest.fixture
def access_token(app, test_user):
    with app.app_context():
        return create_access_token(
            identity=str(test_user.id),
        )


@pytest.fixture
def project(app):
    customer = Customer(
        name="Test Customer",
        email="customer@example.com",
        contact_number="9999999999",
        address="Test Customer Address",
    )

    supplier = Supplier(
        name="Test Supplier",
        email="supplier@example.com",
        contact_number="8888888888",
        address="Test Supplier Address",
    )

    db.session.add_all([customer, supplier])
    db.session.flush()

    project = Project(
        project_title="Test Material Project",
        customer_id=customer.id,
        supplier_id=supplier.id,
    )

    db.session.add(project)
    db.session.commit()

    return project