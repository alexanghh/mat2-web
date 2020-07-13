import os
import base64
import io
import binascii
import zipfile
from uuid import uuid4

from flask import after_this_request, send_from_directory
from flask_restful import Resource, reqparse, abort, request, url_for
from cerberus import Validator
from werkzeug.datastructures import FileStorage
from flasgger import swag_from


from matweb import file_removal_scheduler, utils


class APIUpload(Resource):
    
    def __init__(self, **kwargs):
        self.upload_folder = kwargs['upload_folder']

    @swag_from('./oas/upload.yml')
    def post(self):
        utils.check_upload_folder(self.upload_folder)
        req_parser = reqparse.RequestParser()
        req_parser.add_argument('file_name', type=str, required=True, help='Post parameter is not specified: file_name')
        req_parser.add_argument('file', type=str, required=True, help='Post parameter is not specified: file')

        args = req_parser.parse_args()
        try:
            file_data = base64.b64decode(args['file'])
        except (binascii.Error, ValueError):
            abort(400, message='Failed decoding file')

        file = FileStorage(stream=io.BytesIO(file_data), filename=args['file_name'])
        try:
            filename, filepath = utils.save_file(file, self.upload_folder)
        except ValueError:
            abort(400, message='Invalid Filename')

        parser, mime = utils.get_file_parser(filepath)

        if parser is None:
            abort(415, message='The type %s is not supported' % mime)

        meta = parser.get_meta()
        if not parser.remove_all():
            abort(500, message='Unable to clean %s' % mime)

        key, secret, meta_after, output_filename = utils.cleanup(parser, filepath, self.upload_folder)
        return utils.return_file_created_response(
            utils.get_file_removal_max_age_sec(),
            output_filename,
            mime,
            key,
            secret,
            meta,
            meta_after,
            url_for(
                'apidownload',
                key=key,
                secret=secret,
                filename=output_filename,
                _external=True
            )
        ), 201


class APIDownload(Resource):

    def __init__(self, **kwargs):
        self.upload_folder = kwargs['upload_folder']

    @swag_from('./oas/download.yml')
    def get(self, key: str, secret: str, filename: str):
        complete_path, filepath = utils.is_valid_api_download_file(filename, key, secret, self.upload_folder)
        # Make sure the file is NOT deleted on HEAD requests
        if request.method == 'GET':
            file_removal_scheduler.run_file_removal_job(self.upload_folder)

            @after_this_request
            def remove_file(response):
                if os.path.exists(complete_path):
                    os.remove(complete_path)
                return response

        return send_from_directory(self.upload_folder, filepath, as_attachment=True)


class APIBulkDownloadCreator(Resource):

    def __init__(self, **kwargs):
        self.upload_folder = kwargs['upload_folder']

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
        utils.check_upload_folder(self.upload_folder)
        data = request.json
        if not self.v.validate(data):
            abort(400, message=self.v.errors)
        # prevent the zip file from being overwritten
        zip_filename = 'files.' + str(uuid4()) + '.zip'
        zip_path = os.path.join(self.upload_folder, zip_filename)
        cleaned_files_zip = zipfile.ZipFile(zip_path, 'w')
        with cleaned_files_zip:
            for file_candidate in data['download_list']:
                complete_path, file_path = utils.is_valid_api_download_file(
                    file_candidate['file_name'],
                    file_candidate['key'],
                    file_candidate['secret'],
                    self.upload_folder
                )
                try:
                    cleaned_files_zip.write(complete_path)
                    os.remove(complete_path)
                except ValueError:
                    abort(400, message='Creating the archive failed')

            try:
                cleaned_files_zip.testzip()
            except ValueError as e:
                abort(400, message=str(e))

        parser, mime = utils.get_file_parser(zip_path)
        if not parser.remove_all():
            abort(500, message='Unable to clean %s' % mime)
        key, secret, meta_after, output_filename = utils.cleanup(parser, zip_path, self.upload_folder)
        return {
                   'inactive_after_sec': utils.get_file_removal_max_age_sec(),
                   'output_filename': output_filename,
                   'mime': mime,
                   'key': key,
                   'secret': secret,
                   'meta_after': meta_after,
                   'download_link': url_for(
                       'apidownload',
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
