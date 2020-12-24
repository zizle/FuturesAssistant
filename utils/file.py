# _*_ coding:utf-8 _*_
# @File  : file.py
# @Time  : 2020-12-24 10:14
# @Author: zizle
import os
import random
import string
from configs import FILE_STORAGE


def generate_unique_filename(file_folder, filename, suffix):
    filepath = os.path.join(file_folder, "{}.{}".format(filename, suffix))
    abs_filepath = os.path.join(FILE_STORAGE, filepath)
    if os.path.exists(abs_filepath):
        new_filename_suffix = ''.join(random.sample(string.ascii_letters, 6))
        new_filename = "{}_{}".format(filename, new_filename_suffix)
        return generate_unique_filename(file_folder, new_filename, suffix)
    else:
        return file_folder, filename, suffix
