from flask import Flask
from flask_cors import CORS

from app.config.settings import Config
from app.extensions.api import api
from app.extensions.database import db, migrate
from app.extensions.jwt import jwt


def create_app(config_class=Config):
    app = Flask(__name__)

    app.config.from_object(config_class)
    
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": [
                    "http://localhost:4200",
                ]
            }
        },
    )

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
    from app.routes.customer import customer_bp
    from app.routes.supplier import supplier_bp
    from app.routes.project import project_bp
    from app.routes.customer_query import customer_query_bp
    from app.routes.project_step import project_step_bp
    from app.routes.material import material_bp
    from app.routes.attachment import attachment_bp
    from app.routes.quotation_request import quotation_request_bp
    from app.routes.supplier_quotation import supplier_quotation_bp
    from app.routes.cost_sheet import cost_sheet_bp
    from app.routes.customer_quotation import customer_quotation_bp
    from app.routes.customer_tender import customer_tender_bp
    
    
    api.register_blueprint(auth_bp)
    api.register_blueprint(customer_bp)
    api.register_blueprint(supplier_bp)
    api.register_blueprint(project_bp)
    api.register_blueprint(customer_query_bp)
    api.register_blueprint(project_step_bp)
    api.register_blueprint(material_bp)
    api.register_blueprint(attachment_bp)
    api.register_blueprint(quotation_request_bp)
    api.register_blueprint(supplier_quotation_bp)
    api.register_blueprint(cost_sheet_bp)
    api.register_blueprint(customer_quotation_bp)
    api.register_blueprint(customer_tender_bp)

    return app
