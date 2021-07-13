# _*_ coding:utf-8 _*_
# @File  : exceptions.py
# @Time  : 2021-04-01 08:13
# @Author: zizle

# 自定义错误处理
import traceback
from fastapi import HTTPException
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from logger import logger
from status import r_status


async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    # 自定义处理422验证报错返回信息
    message = ''
    for error in exc.errors():
        message += '.'.join(error.get('loc')) + ':' + error.get('msg') + ";"
    return JSONResponse(
        status_code=200,
        content={'code': r_status.VALIDATE_ERROR, 'message': message}
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    exc_status = exc.status_code
    if exc_status == 401:
        code = r_status.UN_AUTHORIZATION
    else:
        code = r_status.UNKNOWN_ERROR
    return JSONResponse(
        status_code=exc.status_code,
        content={'code': code, 'message': exc.detail}
    )


async def server_error_handler(request: Request, exc: Exception):
    # 自定义处理服务内部出现的错误记录
    text = f'Server Error 500\n\t{request.method} - {request.url}\n\t'
    for e_line in traceback.format_exc().split('\n'):
        if e_line.strip().startswith('File'):
            line_info = [item.replace('"', '').replace(',', '') for item in e_line.strip().split(' ')[1:4]]
            if 'FOUNDATION' in line_info[0]:
                text += ' - '.join(line_info) + '\n\t'
    text += f'{type(exc).__name__}: {exc}'
    logger.error(text)
    return JSONResponse(
        status_code=200,
        content={'code': r_status.SERVER_ERROR, 'message': '服务器内部错误!'}
    )
