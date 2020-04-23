import hmac
import os
import hashlib
import mimetypes as mtype

from flask_restful import abort
from libmat2 import parser_factory
from werkzeug.utils import secure_filename


def get_allow_origin_header_value():
    return os.environ.get('MAT2_ALLOW_ORIGIN_WHITELIST', '*').split(" ")


def hash_file(filepath: str) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            data = f.read(65536)  # read the file by chunk of 64k
            if not data:
                break
            sha256.update(data)
    return sha256.hexdigest()


def check_upload_folder(upload_folder):
    if not os.path.exists(upload_folder):
        os.mkdir(upload_folder)


def return_file_created_response(output_filename, mime, key, meta, meta_after, download_link):
    return {
        'output_filename': output_filename,
        'mime': mime,
        'key': key,
        'meta': meta,
        'meta_after': meta_after,
        'download_link': download_link
    }


def get_supported_extensions():
    extensions = set()
    for parser in parser_factory._get_parsers():
        for m in parser.mimetypes:
            extensions |= set(mtype.guess_all_extensions(m, strict=False))
    # since `guess_extension` might return `None`, we need to filter it out
    return sorted(filter(None, extensions))


def save_file(file, upload_folder):
    filename = secure_filename(file.filename)
    filepath = os.path.join(upload_folder, filename)
    file.save(os.path.join(filepath))
    return filename, filepath


def get_file_parser(filepath: str):
    parser, mime = parser_factory.get_parser(filepath)
    return parser, mime


def cleanup(parser, filepath, upload_folder):
    output_filename = os.path.basename(parser.output_filename)
    parser, _ = parser_factory.get_parser(parser.output_filename)
    meta_after = parser.get_meta()
    os.remove(filepath)

    key = hash_file(os.path.join(upload_folder, output_filename))
    return key, meta_after, output_filename


def get_file_paths(filename, upload_folder):
    filepath = secure_filename(filename)

    complete_path = os.path.join(upload_folder, filepath)
    return complete_path, filepath


def is_valid_api_download_file(filename, key, upload_folder):
    if filename != secure_filename(filename):
        abort(400, message='Insecure filename')

    complete_path, filepath = get_file_paths(filename, upload_folder)

    if not os.path.exists(complete_path):
        abort(404, message='File not found')

    if hmac.compare_digest(hash_file(complete_path), key) is False:
        abort(400, message='The file hash does not match')
    return complete_path, filepath
