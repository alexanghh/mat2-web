import unittest
import tempfile
import shutil
import json
import os

import main


class Mat2APITestCase(unittest.TestCase):
    def setUp(self):
        os.environ.setdefault('MAT2_ALLOW_ORIGIN_WHITELIST', 'origin1.gnu origin2.gnu')
        app = main.create_app()
        self.upload_folder = tempfile.mkdtemp()
        app.config.update(
            TESTING=True,
            UPLOAD_FOLDER=self.upload_folder
        )
        self.app = app.test_client()

    def tearDown(self):
        shutil.rmtree(self.upload_folder)
        if os.environ.get('MAT2_ALLOW_ORIGIN_WHITELIST'):
            del os.environ['MAT2_ALLOW_ORIGIN_WHITELIST']

    def test_api_upload_valid(self):
        request = self.app.post('/api/upload',
                                data='{"file_name": "test_name.jpg", '
                                     '"file": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAf'
                                     'FcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="}',
                                headers={'content-type': 'application/json'}
                                )
        self.assertEqual(request.headers['Content-Type'], 'application/json')
        self.assertEqual(request.headers['Access-Control-Allow-Origin'], 'origin1.gnu')
        self.assertEqual(request.status_code, 200)

        data = json.loads(request.data.decode('utf-8'))
        expected  = {
            'output_filename': 'test_name.cleaned.jpg',
            'mime': 'image/jpeg',
            'key': '81a541f9ebc0233d419d25ed39908b16f82be26a783f32d56c381559e84e6161',
            'meta': {
                'BitDepth': 8,
                'ColorType': 'RGB with Alpha',
                'Compression': 'Deflate/Inflate',
                'Filter': 'Adaptive',
                'Interlace': 'Noninterlaced'
            },
            'meta_after': {},
            'download_link': 'http://localhost/api/download/'
                             '81a541f9ebc0233d419d25ed39908b16f82be26a783f32d56c381559e84e6161/test_name.cleaned.jpg'
        }
        self.assertEqual(data, expected)

    def test_api_upload_missing_params(self):
        request = self.app.post('/api/upload',
                                data='{"file_name": "test_name.jpg"}',
                                headers={'content-type': 'application/json'}
                                )
        self.assertEqual(request.headers['Content-Type'], 'application/json')

        self.assertEqual(request.status_code, 400)
        error = json.loads(request.data.decode('utf-8'))['message']
        self.assertEqual(error['file'], 'Post parameter is not specified: file')

        request = self.app.post('/api/upload',
                                data='{"file_name": "test_name.jpg", "file": "invalid base46 string"}',
                                headers={'content-type': 'application/json'}
                                )
        self.assertEqual(request.headers['Content-Type'], 'application/json')

        self.assertEqual(request.status_code, 400)
        error = json.loads(request.data.decode('utf-8'))['message']
        self.assertEqual(error, 'Failed decoding file: Incorrect padding')

    def test_api_not_supported(self):
        request = self.app.post('/api/upload',
                                data='{"file_name": "test_name.pdf", '
                                     '"file": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAf'
                                     'FcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="}',
                                headers={'content-type': 'application/json'}
                                )
        self.assertEqual(request.headers['Content-Type'], 'application/json')
        self.assertEqual(request.status_code, 415)

        error = json.loads(request.data.decode('utf-8'))['message']
        self.assertEqual(error, 'The type application/pdf is not supported')

    def test_api_supported_extensions(self):
        rv = self.app.get('/api/extension')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.headers['Content-Type'], 'application/json')
        self.assertEqual(rv.headers['Access-Control-Allow-Origin'], 'origin1.gnu')

        extensions = json.loads(rv.data.decode('utf-8'))
        self.assertIn('.pot', extensions)
        self.assertIn('.asc', extensions)
        self.assertIn('.png', extensions)
        self.assertIn('.zip', extensions)

    def test_api_cors_not_set(self):
        del os.environ['MAT2_ALLOW_ORIGIN_WHITELIST']
        app = main.create_app()
        app.config.update(
            TESTING=True
        )
        app = app.test_client()

        rv = app.get('/api/extension')
        self.assertEqual(rv.headers['Access-Control-Allow-Origin'], '*')

    def test_api_cors(self):
        rv = self.app.get('/api/extension')
        self.assertEqual(rv.headers['Access-Control-Allow-Origin'], 'origin1.gnu')

        rv = self.app.get('/api/extension', headers={'Origin': 'origin2.gnu'})
        self.assertEqual(rv.headers['Access-Control-Allow-Origin'], 'origin2.gnu')

        rv = self.app.get('/api/extension', headers={'Origin': 'origin1.gnu'})
        self.assertEqual(rv.headers['Access-Control-Allow-Origin'], 'origin1.gnu')

    def test_api_download(self):
        request = self.app.post('/api/upload',
                                data='{"file_name": "test_name.jpg", '
                                     '"file": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAf'
                                     'FcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="}',
                                headers={'content-type': 'application/json'}
                                )
        self.assertEqual(request.status_code, 200)
        data = json.loads(request.data.decode('utf-8'))

        request = self.app.get('http://localhost/api/download/'
                               '81a541f9ebc0233d419d25ed39908b16f82be26a783f32d56c381559e84e6161/test name.cleaned.jpg')
        self.assertEqual(request.status_code, 400)
        error = json.loads(request.data.decode('utf-8'))['message']
        self.assertEqual(error, 'Insecure filename')

        request = self.app.get('http://localhost/api/download/'
                               '81a541f9ebc0233d419d25ed39908b16f82be26a783f32d56c381559e84e6161/'
                               'wrong_file_name.jpg')
        self.assertEqual(request.status_code, 404)
        error = json.loads(request.data.decode('utf-8'))['message']
        self.assertEqual(error, 'File not found')

        request = self.app.get('http://localhost/api/download/81a541f9e/test_name.cleaned.jpg')
        self.assertEqual(request.status_code, 400)

        error = json.loads(request.data.decode('utf-8'))['message']
        self.assertEqual(error, 'The file hash does not match')

        request = self.app.get(data['download_link'])
        self.assertEqual(request.status_code, 200)


if __name__ == '__main__':
    unittest.main()
