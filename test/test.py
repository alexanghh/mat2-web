import unittest
import tempfile
import shutil
import io
import os

import main


class Mat2WebTestCase(unittest.TestCase):
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

    def test_get_root(self):
        rv = self.app.get('/')
        self.assertIn(b'mat2-web', rv.data)

    def test_check_mimetypes(self):
        rv = self.app.get('/')
        self.assertIn(b'.torrent', rv.data)
        self.assertIn(b'.ods', rv.data)

    def test_get_download_dangerous_file(self):
        rv = self.app.get('/download/1337/\..\filename')
        self.assertEqual(rv.status_code, 302)

    def test_get_download_without_key_file(self):
        rv = self.app.get('/download/non_existant')
        self.assertEqual(rv.status_code, 404)

    def test_get_download_nonexistant_file(self):
        rv = self.app.get('/download/1337/non_existant')
        self.assertEqual(rv.status_code, 302)

    def test_get_upload_without_file(self):
        rv = self.app.post('/')
        self.assertEqual(rv.status_code, 302)

    def test_get_upload_empty_file(self):
        rv = self.app.post('/',
                data=dict(
                    file=(io.BytesIO(b""), 'test.pdf'),
                    ), follow_redirects=False)
        self.assertEqual(rv.status_code, 302)

    def test_get_upload_empty_file_redir(self):
        rv = self.app.post('/',
                data=dict(
                    file=(io.BytesIO(b""), 'test.pdf'),
                    ), follow_redirects=True)
        self.assertIn(b'The type application/pdf is not supported',
                rv.data)
        self.assertEqual(rv.status_code, 200)

    def test_get_upload_no_file_name(self):
        rv = self.app.post('/',
                data=dict(
                    file=(io.BytesIO(b"aaa")),
                    ), follow_redirects=True)
        self.assertIn(b'No file part', rv.data)
        self.assertEqual(rv.status_code, 200)

    def test_get_upload_harmless_file(self):
        rv = self.app.post('/',
                data=dict(
                    file=(io.BytesIO(b"Some text"), 'test.txt'),
                    ), follow_redirects=True)
        self.assertIn(b'/download/4c2e9e6da31a64c70623619c449a040968cdbea85945bf384fa30ed2d5d24fa3/test.cleaned.txt', rv.data)
        self.assertEqual(rv.status_code, 200)
        self.assertNotIn('Access-Control-Allow-Origin', rv.headers)

        rv = self.app.get('/download/4c2e9e6da31a64c70623619c449a040968cdbea85945bf384fa30ed2d5d24fa3/test.cleaned.txt')
        self.assertEqual(rv.status_code, 200)

        rv = self.app.get('/download/4c2e9e6da31a64c70623619c449a040968cdbea85945bf384fa30ed2d5d24fa3/test.cleaned.txt')
        self.assertEqual(rv.status_code, 302)

    def test_upload_wrong_hash(self):
        rv = self.app.post('/',
                           data=dict(
                               file=(io.BytesIO(b"Some text"), 'test.txt'),
                           ), follow_redirects=True)
        self.assertIn(b'/download/4c2e9e6da31a64c70623619c449a040968cdbea85945bf384fa30ed2d5d24fa3/test.cleaned.txt',
                      rv.data)
        self.assertEqual(rv.status_code, 200)

        rv = self.app.get('/download/70623619c449a040968cdbea85945bf384fa30ed2d5d24fa3/test.cleaned.txt')
        self.assertEqual(rv.status_code, 302)


if __name__ == '__main__':
    unittest.main()
