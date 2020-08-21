import os
import jinja2
import yaml

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

    dirname = os.path.dirname(__file__)
    with open(os.path.join(dirname, 'matweb/oas/components.yml')) as file:
        components = yaml.full_load(file)

    template = dict(
        servers=[
            {
                'url': LazyString(lambda: request.host_url),
                'description': 'References the current running server'
            }
        ],
        info={
           'title': 'Mat2 Web API',
           'version': '1',
           'description': 'Mat2 Web RESTful API documentation',
        },
        components=components
    )
    swagger_config = Swagger.DEFAULT_CONFIG
    swagger_config['swagger_ui_bundle_js'] = '//unpkg.com/swagger-ui-dist@3/swagger-ui-bundle.js'
    swagger_config['swagger_ui_standalone_preset_js'] = '//unpkg.com/swagger-ui-dist@3/swagger-ui-standalone-preset.js'
    swagger_config['swagger_ui_css'] = '//unpkg.com/swagger-ui-dist@3/swagger-ui.css'
    swagger_config['openapi'] = "3.0.3"
    Swagger(app, template=template, config=swagger_config)

    CORS(app, resources={r"/api/*": {"origins": utils.get_allow_origin_header_value()}})
    app.logger.info('Matweb started')
    return app


app = create_app()

if __name__ == '__main__':  # pragma: no cover
    app.run()
