# _*_ coding:utf-8 _*_
# @File  : authorization.py
# @Time  : 2021-06-01 11:18
# @Author: zizle

from fastapi import Header
from utils.verify import decipher_user_token


def logged_require(authorization: str = Header(...)):
    print(authorization)
    return decipher_user_token(authorization)
