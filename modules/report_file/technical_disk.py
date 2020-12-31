# _*_ coding:utf-8 _*_
# @File  : technical_disk.py
# @Time  : 2020-12-23 09:48
# @Author: zizle
""" 技术解盘
1. 新建一个技术解盘的文件
2. 根据日期查询技术解盘的文件信息
"""

from fastapi import APIRouter, Form, UploadFile

t_disk_router = APIRouter()


@t_disk_router.post('/technical-disk/', summary='新建技术解盘的pdf文件')
async def post_technical_disk():
    pass

