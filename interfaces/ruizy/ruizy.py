# _*_ coding:utf-8 _*_
# @File  : ruizy.py
# @Time  : 2021-07-13 15:16
# @Author: zizle

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from hutool.security import generate_image_code
from db import RedisConnection

ruizy_api = APIRouter()


@ruizy_api.get('/image-code/', summary='获取图片验证码')
async def get_image_code(img_uuid: str = Query(...)):
    image_buf, text = generate_image_code()
    # 将验证码存入redis
    redis_conn = RedisConnection()
    redis_conn.set_value(key=f'{img_uuid}', value=text, expires=120)
    return StreamingResponse(content=image_buf)
