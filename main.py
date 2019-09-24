import os
import hmac
import mimetypes as mtype
from uuid import uuid4
import jinja2
import base64
import io
import binascii
import zipfile

from cerberus import Validator
import utils
from libmat2 import parser_factory
from flask import Flask, flash, request, redirect, url_for, render_template, send_from_directory, after_this_request
from flask_restful import Resource, Api, reqparse, abort
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask_cors import CORS
from urllib.parse import urljoin


def create_app(test_config=None):
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(32)
    app.config['UPLOAD_FOLDER'] = './uploads/'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    app.config['CUSTOM_TEMPLATES_DIR'] = 'custom_templates'

    app.jinja_loader = jinja2.ChoiceLoader([  # type: ignore
        jinja2.FileSystemLoader(app.config['CUSTOM_TEMPLATES_DIR']),
        app.jinja_loader,
        ])

    api = Api(app)
    CORS(app, resources={r"/api/*": {"origins": utils.get_allow_origin_header_value()}})

    @app.route('/download/<string:key>/<string:filename>')
    def download_file(key:str, filename:str):
        if filename != secure_filename(filename):
            return redirect(url_for('upload_file'))

        complete_path, filepath = get_file_paths(filename)

        if not os.path.exists(complete_path):
            return redirect(url_for('upload_file'))
        if hmac.compare_digest(utils.hash_file(complete_path), key) is False:
            return redirect(url_for('upload_file'))

        @after_this_request
        def remove_file(response):
            os.remove(complete_path)
            return response
        return send_from_directory(app.config['UPLOAD_FOLDER'], filepath)

    @app.route('/', methods=['GET', 'POST'])
    def upload_file():
        utils.check_upload_folder(app.config['UPLOAD_FOLDER'])
        mimetypes = get_supported_extensions()

        if request.method == 'POST':
            if 'file' not in request.files:  # check if the post request has the file part
                flash('No file part')
                return redirect(request.url)

            uploaded_file = request.files['file']
            if not uploaded_file.filename:
                flash('No selected file')
                return redirect(request.url)

            filename, filepath = save_file(uploaded_file)
            parser, mime = get_file_parser(filepath)

            if parser is None:
                flash('The type %s is not supported' % mime)
                return redirect(url_for('upload_file'))

            meta = parser.get_meta()

            if parser.remove_all() is not True:
                flash('Unable to clean %s' % mime)
                return redirect(url_for('upload_file'))

            key, meta_after, output_filename = cleanup(parser, filepath)

            return render_template(
                'download.html', mimetypes=mimetypes, meta=meta, filename=output_filename, meta_after=meta_after, key=key
            )

        max_file_size = int(app.config['MAX_CONTENT_LENGTH'] / 1024 / 1024)
        return render_template('index.html', max_file_size=max_file_size, mimetypes=mimetypes)

    def get_supported_extensions():
        extensions = set()
        for parser in parser_factory._get_parsers():
            for m in parser.mimetypes:
                extensions |= set(mtype.guess_all_extensions(m, strict=False))
        # since `guess_extension` might return `None`, we need to filter it out
        return sorted(filter(None, extensions))

    def save_file(file):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(os.path.join(filepath))
        return filename, filepath

    def get_file_parser(filepath: str):
        parser, mime = parser_factory.get_parser(filepath)
        return parser, mime

    def cleanup(parser, filepath):
        output_filename = os.path.basename(parser.output_filename)
        parser, _ = parser_factory.get_parser(parser.output_filename)
        meta_after = parser.get_meta()
        os.remove(filepath)

        key = utils.hash_file(os.path.join(app.config['UPLOAD_FOLDER'], output_filename))
        return key, meta_after, output_filename

    def get_file_paths(filename):
        filepath = secure_filename(filename)

        complete_path = os.path.join(app.config['UPLOAD_FOLDER'], filepath)
        return complete_path, filepath

    def is_valid_api_download_file(filename, key):
        if filename != secure_filename(filename):
            abort(400, message='Insecure filename')

        complete_path, filepath = get_file_paths(filename)

        if not os.path.exists(complete_path):
            abort(404, message='File not found')

        if hmac.compare_digest(utils.hash_file(complete_path), key) is False:
            abort(400, message='The file hash does not match')
        return complete_path, filepath

    class APIUpload(Resource):

        def post(self):
            utils.check_upload_folder(app.config['UPLOAD_FOLDER'])
            req_parser = reqparse.RequestParser()
            req_parser.add_argument('file_name', type=str, required=True, help='Post parameter is not specified: file_name')
            req_parser.add_argument('file', type=str, required=True, help='Post parameter is not specified: file')

            args = req_parser.parse_args()
            try:
                file_data = base64.b64decode(args['file'])
            except binascii.Error as err:
                abort(400, message='Failed decoding file: ' + str(err))

            file = FileStorage(stream=io.BytesIO(file_data), filename=args['file_name'])
            filename, filepath = save_file(file)
            parser, mime = get_file_parser(filepath)

            if parser is None:
                abort(415, message='The type %s is not supported' % mime)

            meta = parser.get_meta()
            if not parser.remove_all():
                abort(500, message='Unable to clean %s' % mime)

            key, meta_after, output_filename = cleanup(parser, filepath)
            return utils.return_file_created_response(
                output_filename,
                mime,
                key,
                meta,
                meta_after,
                urljoin(request.host_url, '%s/%s/%s/%s' % ('api', 'download', key, output_filename))
            )

    class APIDownload(Resource):
        def get(self, key: str, filename: str):
            complete_path, filepath = is_valid_api_download_file(filename, key)

            @after_this_request
            def remove_file(response):
                os.remove(complete_path)
                return response

            return send_from_directory(app.config['UPLOAD_FOLDER'], filepath)

    class APIBulkDownloadCreator(Resource):
        schema = {
            'download_list': {
                'type': 'list',
                'minlength': 2,
                'maxlength': int(os.environ.get('MAT2_MAX_FILES_BULK_DOWNLOAD', 10)),
                'schema': {
                    'type': 'dict',
                    'schema': {
                        'key': {'type': 'string', 'required': True},
                        'file_name': {'type': 'string', 'required': True}
                    }
                }
            }
        }
        v = Validator(schema)

        def post(self):
            utils.check_upload_folder(app.config['UPLOAD_FOLDER'])
            data = request.json
            if not self.v.validate(data):
                abort(400, message=self.v.errors)
            # prevent the zip file from being overwritten
            zip_filename = 'files.' + str(uuid4()) + '.zip'
            zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
            cleaned_files_zip = zipfile.ZipFile(zip_path, 'w')
            with cleaned_files_zip:
                for file_candidate in data['download_list']:
                    complete_path, file_path = is_valid_api_download_file(
                        file_candidate['file_name'],
                        file_candidate['key']
                    )
                    try:
                        cleaned_files_zip.write(complete_path)
                    except ValueError:
                        abort(400, message='Creating the archive failed')

                try:
                    cleaned_files_zip.testzip()
                except ValueError as e:
                    abort(400, message=str(e))

            parser, mime = get_file_parser(zip_path)
            if not parser.remove_all():
                abort(500, message='Unable to clean %s' % mime)
            key, meta_after, output_filename = cleanup(parser, zip_path)
            return {
                'output_filename': output_filename,
                'mime': mime,
                'key': key,
                'meta_after': meta_after,
                'download_link': urljoin(request.host_url, '%s/%s/%s/%s' % ('api', 'download', key, output_filename))
            }, 201

    class APISupportedExtensions(Resource):
        def get(self):
            return get_supported_extensions()

    api.add_resource(APIUpload, '/api/upload')
    api.add_resource(APIDownload, '/api/download/<string:key>/<string:filename>')
    api.add_resource(APIBulkDownloadCreator, '/api/download/bulk')
    api.add_resource(APISupportedExtensions, '/api/extension')

    return app


app = create_app()

if __name__ == '__main__':  # pragma: no cover
    app.run()
