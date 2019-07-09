import os
import hashlib


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