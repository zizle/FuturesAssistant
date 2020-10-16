# _*_ coding:utf-8 _*_
# @File  : variety.py
# @Time  : 2020-08-10 14:14
# @Author: zizle
""" 品种相关
API-1: 获取分组和分组下的品种
API-2: 获取单个分组下的品种
API-3: 添加一个品种
API-4:
"""
import re
from collections import OrderedDict
from fastapi import APIRouter, Query, Body, HTTPException
from db.mysql_z import MySqlZ
from pymysql.err import IntegrityError, ProgrammingError
from .validate_models import VarietyGroup, VarietyGroupCN, ExchangeLib, ExchangeLibCN, VarietyItem

variety_router = APIRouter()


# 验证品种
def verify_variety(variety_en: str):
    if not re.match(r'^[A-Z]{1,2}$', variety_en):
        raise HTTPException(detail="Invalidate Variety!", status_code=400)
    return variety_en


@variety_router.get("/variety/all/", summary="获取所有分组及旗下的品种")
async def basic_variety_all():
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT `id`,`create_time`,`variety_name`,`variety_en`,`group_name`, `exchange_lib` "
            "FROM `basic_variety` "
            "WHERE `is_active`=1 "
            "ORDER BY `sorted` DESC;",
        )
        all_varieties = cursor.fetchall()
    varieties = OrderedDict()
    for variety_item in all_varieties:
        variety_item['exchange_name'] = ExchangeLibCN[variety_item['exchange_lib']]
        variety_item['group_name'] = VarietyGroupCN[variety_item['group_name']]
        if variety_item['group_name'] not in varieties:
            varieties[variety_item['group_name']] = list()
        varieties[variety_item['group_name']].append(variety_item)
    return {"message": "查询品种信息成功!", "varieties": varieties}


@variety_router.get("/variety/", summary="获取分组下的品种")
async def basic_variety(group: VarietyGroup = Query(...)):
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT `id`,`create_time`,`variety_name`,`variety_en`,`group_name`, `exchange_lib` "
            "FROM `basic_variety` "
            "WHERE `group_name`=%s "
            "ORDER BY `sorted` DESC;",
            (group.name,)
        )
        varieties = cursor.fetchall()
    for variety_item in varieties:
        variety_item['exchange_lib'] = ExchangeLibCN[variety_item['exchange_lib']]
        variety_item['group_name'] = VarietyGroupCN[variety_item['group_name']]

    return {"message": "查询品种信息成功!", "varieties": varieties}


@variety_router.get("/exchange/variety-all/", summary="所有品种以交易所分组")
async def exchange_variety_all():
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id,variety_name,variety_en,exchange_lib,group_name "
            "FROM basic_variety WHERE is_active=1 "
            "ORDER by sorted;"
        )
        all_varieties = cursor.fetchall()
    varieties = OrderedDict()
    for variety_item in all_varieties:
        variety_item['exchange_name'] = ExchangeLibCN[variety_item['exchange_lib']]
        variety_item['group_name_zh'] = VarietyGroupCN[variety_item['group_name']]
        if variety_item['exchange_lib'] not in varieties:
            varieties[variety_item['exchange_lib']] = list()
        varieties[variety_item['exchange_lib']].append(variety_item)
    return {"message": "查询成功!", "varieties": varieties}


@variety_router.post("/variety/", status_code=201, summary="添加品种")
async def add_basic_variety(
        variety: VarietyItem = Body(...)
):
    variety_item = {
        "variety_name": variety.variety_name,
        "variety_en": variety.variety_en,
        "exchange_lib": variety.exchange_lib.name,
        "group_name": variety.group_name.name,
    }
    try:
        with MySqlZ() as cursor:
            cursor.execute(
                "INSERT INTO `basic_variety`"
                "(`variety_name`,`variety_en`,`exchange_lib`,`group_name`) "
                "VALUES (%(variety_name)s,%(variety_en)s,%(exchange_lib)s,%(group_name)s);",
                variety_item
            )
    except IntegrityError:
        raise HTTPException(
            detail="variety_name and variety_en team repeated!",
            status_code=400
        )
    except ProgrammingError:
        raise HTTPException(
            detail="The app inner error.created variety fail!",
            status_code=500
        )
    return {"message": "添加品种成功!", "new_variety": variety}


