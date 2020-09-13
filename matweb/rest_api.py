import os
import base64
import io
import binascii
import zipfile
from uuid import uuid4

from flask import after_this_request, send_from_directory, Blueprint, current_app
from flask_restful import Resource, reqparse, abort, request, url_for, Api
from cerberus import Validator
from werkzeug.datastructures import FileStorage
from flasgger import swag_from


from matweb import file_removal_scheduler, utils


api_bp = Blueprint('api_bp', __name__)
api = Api(api_bp, prefix='/api')


class APIUpload(Resource):
    @swag_from('./oas/upload.yml')
    def post(self):
        utils.check_upload_folder(current_app.config['UPLOAD_FOLDER'])
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('file_name', type=str, required=True, help='Post parameter is not specified: file_name')
        req_parser.add_argument('file', type=str, required=True, help='Post parameter is not specified: file')

        args = req_parser.parse_args()
        try:
            file_data = base64.b64decode(args['file'])
        except (binascii.Error, ValueError) as e:
            current_app.logger.error('Upload - Decoding base64 file %s', e)
            abort(400, message='Failed decoding file')

        file = FileStorage(stream=io.BytesIO(file_data), filename=args['file_name'])
        try:
            filename, filepath = utils.save_file(file, current_app.config['UPLOAD_FOLDER'])
        except ValueError:
            current_app.logger.error('Upload - Invalid file name')
            abort(400, message='Invalid Filename')

        parser, mime = utils.get_file_parser(filepath)

        if parser is None:
            current_app.logger.error('Upload - Invalid mime type %s', mime)
            abort(415, message='The type %s is not supported' % mime)
        try:
            if not parser.remove_all():
                raise ValueError()
            meta = parser.get_meta()
            key, secret, meta_after, output_filename = utils.cleanup(parser, filepath,
                                                                     current_app.config['UPLOAD_FOLDER'])
            return utils.return_file_created_response(
                utils.get_file_removal_max_age_sec(),
                output_filename,
                mime,
                key,
                secret,
                meta,
                meta_after,
                url_for(
                    'api_bp.apidownload',
                    key=key,
                    secret=secret,
                    filename=output_filename,
                    _external=True
                )
            ), 201
        except (ValueError, RuntimeError) as e:
            current_app.logger.error('Upload - Cleaning failed with mime: %s', mime)
            abort(400, message='Unable to clean %s' % mime)


class APIDownload(Resource):
    @swag_from('./oas/download.yml')
    def get(self, key: str, secret: str, filename: str):
        complete_path, filepath = utils.is_valid_api_download_file(filename, key, secret, current_app.config['UPLOAD_FOLDER'])
        # Make sure the file is NOT deleted on HEAD requests
        if request.method == 'GET':
            file_removal_scheduler.run_file_removal_job(current_app.config['UPLOAD_FOLDER'])

            @after_this_request
            def remove_file(response):
                if os.path.exists(complete_path):
                    os.remove(complete_path)
                return response

        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filepath, as_attachment=True)


class APIClean(Resource):
    @swag_from('./oas/remove_metadata.yml')
    def post(self):
        if 'file' not in request.files:
            current_app.logger.error('Clean - No file part')
            abort(400, message='No file part')

        uploaded_file = request.files['file']
        if not uploaded_file.filename:
            current_app.logger.error('Clean - No selected `file`')
            abort(400, message='No selected `file`')
        try:
            filename, filepath = utils.save_file(uploaded_file, current_app.config['UPLOAD_FOLDER'])
        except ValueError:
            current_app.logger.error('Clean - Invalid Filename')
            abort(400, message='Invalid Filename')

        parser, mime = utils.get_file_parser(filepath)

        if parser is None:
            current_app.logger.error('Clean - The type %s is not supported', mime)
            abort(415, message='The type %s is not supported' % mime)

        if parser.remove_all() is not True:
            current_app.logger.error('Clean - Unable to clean %s', mime)
            abort(500, message='Unable to clean %s' % mime)

        _, _, _, output_filename = utils.cleanup(parser, filepath, current_app.config['UPLOAD_FOLDER'])

        @after_this_request
        def remove_file(response):
            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], output_filename))
            return response

        return send_from_directory(current_app.config['UPLOAD_FOLDER'], output_filename, as_attachment=True)


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
                    'secret': {'type': 'string', 'required': True},
                    'file_name': {'type': 'string', 'required': True}
                }
            }
        }
    }
    v = Validator(schema)

    @swag_from('./oas/bulk.yml')
    def post(self):
        utils.check_upload_folder(current_app.config['UPLOAD_FOLDER'])
        data = request.json
        if not data:
            abort(400, message="Post Body Required")
            current_app.logger.error('BulkDownload -  Missing Post Body')
        if not self.v.validate(data):
            current_app.logger.error('BulkDownload -  Missing Post Body: %s', str(self.v.errors))
            abort(400, message=self.v.errors)
        # prevent the zip file from being overwritten
        zip_filename = 'files.' + str(uuid4()) + '.zip'
        zip_path = os.path.join(current_app.config['UPLOAD_FOLDER'], zip_filename)
        cleaned_files_zip = zipfile.ZipFile(zip_path, 'w')
        with cleaned_files_zip:
            for file_candidate in data['download_list']:
                complete_path, file_path = utils.is_valid_api_download_file(
                    file_candidate['file_name'],
                    file_candidate['key'],
                    file_candidate['secret'],
                    current_app.config['UPLOAD_FOLDER']
                )
                try:
                    cleaned_files_zip.write(complete_path)
                    os.remove(complete_path)
                except ValueError as e:
                    current_app.logger.error('BulkDownload -  Creating archive failed: %s', e)
                    abort(400, message='Creating the archive failed')

            try:
                cleaned_files_zip.testzip()
            except ValueError as e:
                current_app.logger.error('BulkDownload -  Validating Zip failed: %s', e)
                abort(400, message='Validating Zip failed')

        parser, mime = utils.get_file_parser(zip_path)
        if not parser.remove_all():
            current_app.logger.error('BulkDownload -  Unable to clean Zip')
            abort(500, message='Unable to clean %s' % mime)
        key, secret, meta_after, output_filename = utils.cleanup(parser, zip_path, current_app.config['UPLOAD_FOLDER'])
        return {
                   'inactive_after_sec': utils.get_file_removal_max_age_sec(),
                   'output_filename': output_filename,
                   'mime': mime,
                   'key': key,
                   'secret': secret,
                   'meta_after': meta_after,
                   'download_link': url_for(
                       'api_bp.apidownload',
                       key=key,
                       secret=secret,
                       filename=output_filename,
                       _external=True
                   )
               }, 201


class APISupportedExtensions(Resource):
    @swag_from('./oas/extension.yml')
    def get(self):
        return utils.get_supported_extensions()


api.add_resource(
        APIUpload,
        '/upload'
    )
api.add_resource(
    APIDownload,
    '/download/<string:key>/<string:secret>/<string:filename>'
)
api.add_resource(
    APIClean,
    '/remove_metadata'
)
api.add_resource(
    APIBulkDownloadCreator,
    '/download/bulk'
)
api.add_resource(APISupportedExtensions, '/extension')
