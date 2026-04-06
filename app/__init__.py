from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name="default"):
    app = Flask(__name__)

    from config import config
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from app.blueprints.main import main as main_bp
    app.register_blueprint(main_bp)

    from app.blueprints.movements import movements as movements_bp
    app.register_blueprint(movements_bp, url_prefix="/movimientos")

    from app.blueprints.categories import categories as categories_bp
    app.register_blueprint(categories_bp, url_prefix="/categorias")

    # Register error handlers
    from app.blueprints.errors import errors as errors_bp
    app.register_blueprint(errors_bp)

    # Register template filters
    from app.utils import format_currency, format_date
    app.jinja_env.filters["currency"] = format_currency
    app.jinja_env.filters["date_fmt"] = format_date

    return app
