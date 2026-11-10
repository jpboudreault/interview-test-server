import logging

from flask import Flask

from .config import Config
from .routes import api


def create_app(config: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config)
    if not app.config["TAX_API_URL"]:
        raise RuntimeError("Set TAX_API_URL, e.g. https://{app-name}.fly.dev")

    logging.basicConfig(
        level=app.config["LOG_LEVEL"],
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    app.register_blueprint(api, url_prefix="/api")
    return app
