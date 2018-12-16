import unittest

import main


class FlaskrTestCase(unittest.TestCase):
    def setUp(self):
        main.app.testing = True
        self.app = main.app.test_client()

    def test_get_root(self):
        rv = self.app.get('/')
        self.assertIn(b'mat2-web', rv.data)

    def test_get_download_dangerous_file(self):
        rv = self.app.get('/download/\..\filename')
        self.assertEqual(rv.status_code, 302)

    def test_get_download_nonexistant_file(self):
        rv = self.app.get('/download/non_existant')
        self.assertEqual(rv.status_code, 302)

if __name__ == '__main__':
    unittest.main()

