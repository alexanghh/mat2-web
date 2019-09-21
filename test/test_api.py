import unittest
import tempfile
import json
import os
import shutil

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
        expected = {
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

        request = self.app.get(data['download_link'])
        self.assertEqual(request.status_code, 404)

    def test_api_bulk_download(self):
        request = self.app.post('/api/upload',
                                data='{"file_name": "test_name.jpg", '
                                     '"file": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAf'
                                     'FcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="}',
                                headers={'content-type': 'application/json'}
                                )
        self.assertEqual(request.status_code, 200)
        upload_one = json.loads(request.data.decode('utf-8'))

        request = self.app.post('/api/upload',
                                data='{"file_name": "test_name_two.jpg", '
                                     '"file": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42'
                                     'mO0vqpQDwAENAGxOnU0jQAAAABJRU5ErkJggg=="}',
                                headers={'content-type': 'application/json'}
                                )
        self.assertEqual(request.status_code, 200)
        upload_two = json.loads(request.data.decode('utf-8'))

        post_body = {
            u'download_list': [
                {
                    u'file_name': upload_one['output_filename'],
                    u'key': upload_one['key']
                },
                {
                    u'file_name': upload_two['output_filename'],
                    u'key': upload_two['key']
                }
            ]
        }
        request = self.app.post('/api/download/bulk',
                                data=json.dumps(post_body),
                                headers={'content-type': 'application/json'}
                                )

        response = json.loads(request.data.decode('utf-8'))
        self.assertEqual(request.status_code, 201)

        self.assertIn(
            "http://localhost/api/download/",
            response['download_link']
        )
        self.assertIn(
            ".cleaned.zip",
            response['download_link']
        )

        self.assertIn('files.', response['output_filename'])
        self.assertIn('cleaned.zip', response['output_filename'])
        self.assertIn(response['mime'], 'application/zip')
        self.assertEqual(response['meta_after'], {})

        request = self.app.get(response['download_link'])
        self.assertEqual(request.status_code, 200)

        request = self.app.get(response['download_link'])
        self.assertEqual(request.status_code, 404)

    def test_api_bulk_download_validation(self):
        post_body = {
            u'download_list': [
                {
                    u'file_name': 'invalid_file_name',
                    u'key': 'invalid_key'
                }
            ]
        }
        request = self.app.post('/api/download/bulk',
                                data=json.dumps(post_body),
                                headers={'content-type': 'application/json'}
                                )

        response = json.loads(request.data.decode('utf-8'))
        self.assertEqual(response['message']['download_list'][0], 'min length is 2')
        self.assertEqual(request.status_code, 400)

        post_body = {
            u'download_list': [
                {
                    u'file_name': 'test.jpg',
                    u'key': 'key'
                },
                {
                    u'file_name': 'test.jpg',
                    u'key': 'key'
                },
                {
                    u'file_name': 'test.jpg',
                    u'key': 'key'
                },
                {
                    u'file_name': 'test.jpg',
                    u'key': 'key'
                },
                {
                    u'file_name': 'test.jpg',
                    u'key': 'key'
                },
                {
                    u'file_name': 'test.jpg',
                    u'key': 'key'
                },
                {
                    u'file_name': 'test.jpg',
                    u'key': 'key'
                },
                {
                    u'file_name': 'test.jpg',
                    u'key': 'key'
                },
                {
                    u'file_name': 'test.jpg',
                    u'key': 'key'
                },
                {
                    u'file_name': 'test.jpg',
                    u'key': 'key'
                },
                {
                    u'file_name': 'test.jpg',
                    u'key': 'key'
                }
            ]
        }
        request = self.app.post('/api/download/bulk',
                                data=json.dumps(post_body),
                                headers={'content-type': 'application/json'}
                                )

        response = json.loads(request.data.decode('utf-8'))
        self.assertEqual(response['message']['download_list'][0], 'max length is 10')
        self.assertEqual(request.status_code, 400)

        post_body = {
            u'download_list': [
                {
                    u'file_name_x': 'invalid_file_name',
                    u'key_x': 'invalid_key'
                },
                {
                    u'file_name_x': 'invalid_file_name',
                    u'key_x': 'invalid_key'
                }
            ]
        }
        request = self.app.post('/api/download/bulk',
                                data=json.dumps(post_body),
                                headers={'content-type': 'application/json'}
                                )

        response = json.loads(request.data.decode('utf-8'))
        expected = {
            'message': {
                'download_list': [
                    {
                        '0': [{
                            'file_name_x': ['unknown field'],
                            'key_x': ['unknown field']
                        }],
                        '1': [{
                            'file_name_x': ['unknown field'],
                            'key_x': ['unknown field']
                        }]
                    }
                ]
            }
        }
        self.assertEqual(response, expected)
        self.assertEqual(request.status_code, 400)

        post_body = {
            u'download_list': [
                {
                    u'file_name': 'invalid_file_name1',
                    u'key': 'invalid_key1'
                },
                {
                    u'file_name': 'invalid_file_name2',
                    u'key': 'invalid_key2'
                }
            ]
        }
        request = self.app.post('/api/download/bulk',
                                data=json.dumps(post_body),
                                headers={'content-type': 'application/json'}
                                )
        response = json.loads(request.data.decode('utf-8'))
        self.assertEqual('File not found', response['message'])


if __name__ == '__main__':
    unittest.main()
