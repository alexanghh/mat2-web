import unittest
import tempfile
from os import path, environ
import shutil

import file_removal_scheduler
import main


class Mat2WebTestCase(unittest.TestCase):
    def setUp(self):
        self.upload_folder = tempfile.mkdtemp()
        app = main.create_app()
        app.config.update(
            TESTING=True,
            UPLOAD_FOLDER=self.upload_folder
        )
        self.app = app

    def test_removal(self):
        filename = 'test_name.cleaned.jpg'
        environ['MAT2_MAX_FILE_AGE_FOR_REMOVAL'] = '0'
        open(path.join(self.upload_folder, filename), 'a').close()
        self.assertTrue(path.exists(path.join(self.upload_folder, )))
        for i in range(0, 11):
            file_removal_scheduler.run_file_removal_job(self.app.config['UPLOAD_FOLDER'])
        self.assertFalse(path.exists(path.join(self.upload_folder, filename)))

        open(path.join(self.upload_folder, filename), 'a').close()
        file_removal_scheduler.run_file_removal_job(self.app.config['UPLOAD_FOLDER'])
        self.assertTrue(path.exists(path.join(self.upload_folder, )))

    def test_non_removal(self):
        filename = u'i_should_no_be_removed.txt'
        environ['MAT2_MAX_FILE_AGE_FOR_REMOVAL'] = '9999999'
        open(path.join(self.upload_folder, filename), 'a').close()
        self.assertTrue(path.exists(path.join(self.upload_folder, filename)))
        for i in range(0, 11):
            file_removal_scheduler.run_file_removal_job(self.app.config['UPLOAD_FOLDER'])
        self.assertTrue(path.exists(path.join(self.upload_folder, filename)))

    def tearDown(self):
        shutil.rmtree(self.upload_folder)


if __name__ == '__main__':
    unittest.main()

