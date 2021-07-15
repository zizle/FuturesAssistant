# _*_ coding:utf-8 _*_
# @File  : depends.py
# @Time  : 2021-04-01 15:38
# @Author: zizle
import datetime

from fastapi import Cookie, Header, HTTPException, Query
from hutool.security import decrypt_access_token
from configs import ADMIN_FLAG


# 解析cookie或headers中的Authorization字段并验证是否登录(Cookie在FastAPI中被解析为查询参数一样的用法)
# headers再FastAPI与Query,Cookies等一样的用法且自动转义小写,中横线转为下划线
async def logged_require(authorization: str = Header('')):
    person = decrypt_access_token(authorization)
    if not person:
        raise HTTPException(status_code=401, detail='Un Authorization!')
    return person


async def admin_logged_require(authorization: str = Header('')):
    person = decrypt_access_token(authorization)
    if not person or ADMIN_FLAG not in person['access']:
        raise HTTPException(status_code=401, detail='Un Authorization!')
    return person


# 日期验证
async def verify_date(date: str = Query(...)) -> datetime.datetime:
    try:
        strp_date = datetime.datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=422, detail='params can not format %Y-%m-%d!')
    return strp_date


# 日期开始
async def require_start_date(ds: str = Query(...)) -> datetime.datetime:
    try:
        ds = datetime.datetime.strptime(ds, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=422, detail='params ds can not format %Y-%m-%d!')
    return ds


# 日期结束
async def require_end_date(de: str = Query(...)) -> datetime.datetime:
    try:
        de = datetime.datetime.strptime(de, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=422, detail='params de can not format %Y-%m-%d!')
    return de
