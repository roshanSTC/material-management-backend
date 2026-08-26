from flask import Flask

from app.config.settings import Config
from app.extensions.api import api
from app.extensions.database import db, migrate
from app.extensions.jwt import jwt


def create_app(config_class=Config):
    app = Flask(__name__)

    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    api.init_app(app)

    from app.models import (
        Customer,
        CustomerQuery,
        CustomerQueryItem,
        Project,
        Supplier,
        User,
        Role,
        Permission,
    )   # noqa: F401
    
    from app.routes.auth import auth_bp

    api.register_blueprint(auth_bp)

    return app