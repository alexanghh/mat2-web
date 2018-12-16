import unittest
import tempfile
import shutil
import io

import main


class FlaskrTestCase(unittest.TestCase):
    def setUp(self):
        main.app.testing = True
        main.app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
        self.app = main.app.test_client()

    def tearDown(self):
        shutil.rmtree(main.app.config['UPLOAD_FOLDER'])

    def test_get_root(self):
        rv = self.app.get('/')
        self.assertIn(b'mat2-web', rv.data)

    def test_check_mimetypes(self):
        rv = self.app.get('/')
        self.assertIn(b'application/zip', rv.data)
        self.assertIn(b'audio/x-flac', rv.data)

    def test_get_download_dangerous_file(self):
        rv = self.app.get('/download/\..\filename')
        self.assertEqual(rv.status_code, 302)

    def test_get_download_nonexistant_file(self):
        rv = self.app.get('/download/non_existant')
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
                    file=(io.BytesIO(b"aaa"), ''),
                    ), follow_redirects=True)
        self.assertIn(b'No file part', rv.data)
        self.assertEqual(rv.status_code, 200)


    def test_get_upload_harmless_file(self):
        rv = self.app.post('/',
                data=dict(
                    file=(io.BytesIO(b"Some text"), 'test.txt'),
                    ), follow_redirects=True)
        self.assertIn(b'/download/test.cleaned.txt', rv.data)
        self.assertEqual(rv.status_code, 200)

        rv = self.app.get('/download/test.cleaned.txt')
        self.assertEqual(rv.status_code, 200)

        rv = self.app.get('/download/test.cleaned.txt')
        self.assertEqual(rv.status_code, 302)


if __name__ == '__main__':
    unittest.main()

