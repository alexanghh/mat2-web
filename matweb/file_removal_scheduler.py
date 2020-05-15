import glob
import time
import sys
import os
import random

from matweb import utils


def run_file_removal_job(upload_folder_path):
    if random.randint(0, 10) == 0:
        for file in glob.glob(upload_folder_path + '/*'):
            delete_file_when_too_old(file)


def delete_file_when_too_old(filepath):
    file_mod_time = os.stat(filepath).st_mtime

    # time in second since last modification of file
    last_time = time.time() - file_mod_time

    # if file is older than our configured max timeframe, delete it
    if last_time > utils.get_file_removal_max_age_sec():
        try:
            os.remove(filepath)
        except OSError:
            print('Automatic File Removal failed on file: ' + str(filepath))
            sys.exit(1)
