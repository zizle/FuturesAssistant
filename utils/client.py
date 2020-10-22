# _*_ coding:utf-8 _*_
# @File  : client.py
# @Time  : 2020-08-31 8:59
# @Author: zizle


def encryption_uuid(raw_uuid):
    """ 加密UUID """
    secret_str = ""
    for c_str in raw_uuid:
        if c_str.isdigit():  # 数字
            secret_str += str(int(c_str) + 8)[-1]
        elif c_str.isalpha():  # 字母
            secret_str += chr(ord(c_str) + 8).upper()
        else:
            secret_str += c_str
    return secret_str


def decipher_uuid(secret_uuid):
    """ 解密uuid """
    raw_str = ""
    for c_str in secret_uuid:
        if c_str.isdigit():  # 数字
            raw_str += str(int(c_str) - 8)[-1]
        elif c_str.isalpha():  # 字母
            raw_str += chr(ord(c_str) - 8).upper()
        else:
            raw_str += c_str
    return raw_str
