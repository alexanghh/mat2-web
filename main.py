import os
import jinja2

from matweb import utils, rest_api, frontend
from flask import Flask, request
from flask_cors import CORS
from flasgger import Swagger, LazyString, LazyJSONEncoder


def create_app(test_config=None):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(32)
    app.config['UPLOAD_FOLDER'] = os.environ.get('MAT2_WEB_DOWNLOAD_FOLDER', './uploads/')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    app.config['CUSTOM_TEMPLATES_DIR'] = 'custom_templates'
    # optionally load settings from config.py
    app.config.from_object('config')

    if test_config is not None:
        app.config.update(test_config)

    # Non JS Frontend
    app.jinja_loader = jinja2.ChoiceLoader([  # type: ignore
        jinja2.FileSystemLoader(app.config['CUSTOM_TEMPLATES_DIR']),
        app.jinja_loader,
    ])
    app.register_blueprint(frontend.routes)

    # Restful API hookup
    app.register_blueprint(rest_api.api_bp)
    app.json_encoder = LazyJSONEncoder

    template = dict(
        swaggerUiPrefix=LazyString(lambda: request.environ.get('HTTP_X_SCRIPT_NAME', '')),
        schemes=['https', 'http'],
        version='1',
        host=LazyString(lambda: request.host),
        basePath='/',
        info={
           'title': 'Mat2 Web API',
           'version': '1',
           'description': 'Mat2 Web RESTful API documentation',
        }
    )
    Swagger(app, template=template)
    CORS(app, resources={r"/api/*": {"origins": utils.get_allow_origin_header_value()}})

    return app


app = create_app()

if __name__ == '__main__':  # pragma: no cover
    app.run()
