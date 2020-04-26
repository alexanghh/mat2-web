import os
import jinja2

from matweb import utils, rest_api, frontend
from flask import Flask
from flask_restful import Api
from flask_cors import CORS


def create_app(test_config=None):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(32)
    app.config['UPLOAD_FOLDER'] = './uploads/'
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
    api = Api(app)
    CORS(app, resources={r"/api/*": {"origins": utils.get_allow_origin_header_value()}})
    api.add_resource(
        rest_api.APIUpload,
        '/api/upload',
        resource_class_kwargs={'upload_folder': app.config['UPLOAD_FOLDER']}
    )
    api.add_resource(
        rest_api.APIDownload,
        '/api/download/<string:key>/<string:secret>/<string:filename>',
        resource_class_kwargs={'upload_folder': app.config['UPLOAD_FOLDER']}
    )
    api.add_resource(
        rest_api.APIBulkDownloadCreator,
        '/api/download/bulk',
        resource_class_kwargs={'upload_folder': app.config['UPLOAD_FOLDER']}
    )
    api.add_resource(rest_api.APISupportedExtensions, '/api/extension')

    return app


app = create_app()

if __name__ == '__main__':  # pragma: no cover
    app.run()
