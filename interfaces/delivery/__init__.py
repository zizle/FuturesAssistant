# _*_ coding:utf-8 _*_
# @File  : __init__.py.py
# @Time  : 2020-09-22 13:25
# @Author: zizle
from fastapi import APIRouter
from .warehouse import warehouse_router
from .discussion import discussion_router
from .receipt import receipt_router

delivery_router = APIRouter()
delivery_router.include_router(warehouse_router)
delivery_router.include_router(discussion_router)
delivery_router.include_router(receipt_router)
