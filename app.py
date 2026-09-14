import os

from flask import Flask, g

from src.database import SessionLocal, init_db
from src.routes import register_routes


def create_app():
    app = Flask(__name__, template_folder="Frontend", static_folder="Frontend")
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-not-for-production")
    init_db()

    @app.before_request
    def open_session():
        g.db = SessionLocal()

    @app.teardown_appcontext
    def close_session(exception=None):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    register_routes(app)
    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
