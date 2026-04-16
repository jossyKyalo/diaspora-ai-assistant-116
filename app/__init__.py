from flask import Flask
from flask_cors import CORS
from config import Config


def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(Config)
    CORS(app)

    from app.blueprints.tasks import tasks_bp
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.messages import messages_bp

    app.register_blueprint(tasks_bp, url_prefix="/tasks")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(messages_bp, url_prefix="/messages")

    from flask import redirect, url_for

    @app.route("/")
    def index():
        return redirect(url_for("dashboard.index"))

    return app
