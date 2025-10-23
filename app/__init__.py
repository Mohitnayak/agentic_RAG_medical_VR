from flask import Flask, render_template
from flask_cors import CORS
from .config import Config
from .models import db


def create_app() -> Flask:
    # Point Flask to project-level templates/static
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config.from_object(Config)

    # Extensions
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)

    # Blueprints
    from .routes import api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.route("/healthz", methods=["GET"])  # lightweight health endpoint
    def healthz():
        return {"status": "ok"}, 200

    @app.route("/")
    def index():
        return render_template("scene.html")

    return app


