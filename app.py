# _*_ coding:utf-8 _*_
# @File  : app.py
# @Time  : 2021-07-13 15:52
# @Author: zizle

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from configs import FILE_STORAGE
from interfaces import interface_api
# 连接数据库连接池
from db import FAConnection


app = FastAPI()


def create_app():
    mount_static()  # 挂载静态文件
    add_middleware()  # 添加中间件
    add_routers()  # 添加路由
    return app


def mount_static():
    app.mount("/static/", StaticFiles(directory=FILE_STORAGE), name="staticFiles")


def add_middleware():
    # 添加框架中有的中间件 allow_credentials=True允许携带cookie，此时allow_origins不能为["*"]
    app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_credentials=False, allow_methods=["*"],
                       allow_headers=['*'])


def add_routers():
    # 添加api接口路由
    app.include_router(interface_api, prefix='/api')
