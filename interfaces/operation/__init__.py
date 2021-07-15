# _*_ coding:utf-8 _*_
# @File  : __init__.py.py
# @Time  : 2021-06-10 15:05
# @Author: zizle

# 运营管理
from fastapi import APIRouter
from .client_op import op_client_api
from .user_op import op_user_api
from .variety_op import op_variety_api
from .menu_op import op_menu_api

operation_router = APIRouter()
operation_router.include_router(op_client_api)
operation_router.include_router(op_user_api)
operation_router.include_router(op_variety_api)
operation_router.include_router(op_menu_api)
