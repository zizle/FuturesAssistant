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
import os
import re
import hashlib
from datetime import datetime, timedelta
from collections import OrderedDict
from fastapi import APIRouter, Query, Body, HTTPException, Depends, UploadFile, Form
from db.mysql_z import MySqlZ, ExchangeLibDB
from db.redis_z import RedisZ
from pymysql.err import IntegrityError, ProgrammingError
from .validate_models import VarietyGroup, VarietyGroupCN, ExchangeLib, ExchangeLibCN, VarietyItem
from configs import FILE_STORAGE

variety_router = APIRouter()


# 验证品种
def verify_variety(variety_en: str):
    if not re.match(r'^[A-Z]{1,2}$', variety_en):
        raise HTTPException(detail="Invalidate Variety!", status_code=400)
    return variety_en


# 过滤非交易所的品种
def filter_exchange_others(variety_item):
    if variety_item["variety_en"] in ['GP', 'GZ', 'WB', 'HG']:
        return False
    return True


# 过滤掉金融的交易所品种(使用早期设置的)
def filter_cffex_real(variety_item):
    if variety_item["variety_en"] in ['IF', 'IH', 'IC', 'TS', 'TF', 'T']:
        return False
    return True


@variety_router.get("/variety-en-sorted/", summary='获取以交易代码排序的所有品种')
async def variety_en_sorted(is_real: int = Query(2, le=2, ge=0)):
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT `variety_name`,`variety_en`,`group_name`, `exchange_lib` "
            "FROM `basic_variety` "
            "WHERE `is_active`=1 "
            "ORDER BY `variety_en`;",
        )
        all_varieties = cursor.fetchall()
    if is_real == 1:
        all_varieties = list(filter(filter_exchange_others, all_varieties))
    elif is_real == 2:
        all_varieties = list(filter(filter_cffex_real, all_varieties))
    else:
        pass
    for variety_item in all_varieties:
        variety_item['exchange_name'] = ExchangeLibCN[variety_item['exchange_lib']]
        variety_item['group_name'] = VarietyGroupCN[variety_item['group_name']]
    return {"message": "查询品种信息成功!", "varieties": all_varieties}


# 由于系统首次设计把金融品种分为股指，国债，宏观等品种与交易所不符合，所以出现了is_real参数
@variety_router.get("/variety/all/", summary="获取所有分组及旗下的品种")
async def basic_variety_all(is_real: int = Query(2, le=2, ge=0)):
    # is_real == 0 不做过滤
    # is_real == 1 过滤掉非交易所的(早期设置的金融品种)
    # is_real == 2 过滤掉真正的金融品种
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT `id`,`create_time`,`variety_name`,`variety_en`,`group_name`, `exchange_lib` "
            "FROM `basic_variety` "
            "WHERE `is_active`=1 "
            "ORDER BY `sorted` DESC;",
        )
        all_varieties = cursor.fetchall()
    if is_real == 1:
        all_varieties = list(filter(filter_exchange_others, all_varieties))
    elif is_real == 2:
        all_varieties = list(filter(filter_cffex_real, all_varieties))
    else:
        pass
    varieties = OrderedDict()
    for variety_item in all_varieties:
        variety_item['exchange_name'] = ExchangeLibCN[variety_item['exchange_lib']]
        variety_item['group_name'] = VarietyGroupCN[variety_item['group_name']]
        if variety_item['group_name'] not in varieties:
            varieties[variety_item['group_name']] = list()
        varieties[variety_item['group_name']].append(variety_item)
    return {"message": "查询品种信息成功!", "varieties": varieties}


@variety_router.get("/variety/", summary="获取分组下的品种")
async def basic_variety(group: VarietyGroup = Query(...), is_real: int = Query(2, ge=0, le=2)):
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT `id`,`create_time`,`variety_name`,`variety_en`,`group_name`, `exchange_lib` "
            "FROM `basic_variety` "
            "WHERE `group_name`=%s "
            "ORDER BY `sorted` DESC;",
            (group.name,)
        )
        varieties = cursor.fetchall()
    if is_real == 1:
        varieties = list(filter(filter_exchange_others, varieties))
    elif is_real == 2:
        varieties = list(filter(filter_cffex_real, varieties))
    else:
        pass
    for variety_item in varieties:
        variety_item['exchange_lib'] = ExchangeLibCN[variety_item['exchange_lib']]
        variety_item['group_name'] = VarietyGroupCN[variety_item['group_name']]

    return {"message": "查询品种信息成功!", "varieties": varieties}


@variety_router.get("/exchange-variety/", summary="获取交易所下的品种")
async def basic_variety(exchange: ExchangeLib = Query(...), is_real: int = Query(2, ge=0, le=2)):
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT `id`,`create_time`,`variety_name`,`variety_en`,`group_name`, `exchange_lib` "
            "FROM `basic_variety` "
            "WHERE `exchange_lib`=%s "
            "ORDER BY `sorted` DESC;",
            (exchange.name,)
        )
        varieties = cursor.fetchall()
    if is_real == 1:
        varieties = list(filter(filter_exchange_others, varieties))
    elif is_real == 2:
        varieties = list(filter(filter_cffex_real, varieties))
    else:
        pass
    for variety_item in varieties:
        variety_item['exchange_lib'] = ExchangeLibCN[variety_item['exchange_lib']]
        variety_item['group_name'] = VarietyGroupCN[variety_item['group_name']]

    return {"message": "查询品种信息成功!", "varieties": varieties}


@variety_router.get("/exchange/variety-all/", summary="所有品种以交易所分组")
async def exchange_variety_all(is_real: int = Query(2, le=2, ge=0)):
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id,variety_name,variety_en,exchange_lib,group_name "
            "FROM basic_variety WHERE is_active=1 "
            "ORDER by sorted;"
        )
        all_varieties = cursor.fetchall()
    if is_real == 1:
        all_varieties = list(filter(filter_exchange_others, all_varieties))
    elif is_real == 2:
        all_varieties = list(filter(filter_cffex_real, all_varieties))
    else:
        pass
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


@variety_router.get("/{variety_en}/contract/", summary="获取品种的合约")
async def variety_all_contract(variety_en: str = Depends(verify_variety)):
    # 获取redis中存储的合约
    with RedisZ() as r_redis:
        contracts = r_redis.get("{}_contract".format(variety_en))
        if not contracts:  # 没有获取到合约
            # 查询品种所属的交易所
            with MySqlZ() as m_cursor:
                m_cursor.execute("SELECT exchange_lib,variety_en FROM basic_variety WHERE variety_en=%s;", (variety_en, ))
                variety_obj = m_cursor.fetchone()
                if not variety_obj:
                    raise HTTPException(status_code=400, detail="Variety Error!")
                # 查询品种的最近一天所有合约
                table_name = "{}_daily".format(variety_obj["exchange_lib"])
                query_sql = "SELECT variety_en,contract FROM {} WHERE " \
                            "`date`=(SELECT MAX(`date`) FROM {}) AND variety_en=%s " \
                            "GROUP BY contract;".format(table_name, table_name)
                with ExchangeLibDB() as ex_cursor:
                    ex_cursor.execute(query_sql, (variety_en, ))
                    all_contract = ex_cursor.fetchall()
            # 将数据存入redis
            current_time = datetime.now()
            next_day = datetime.strptime(current_time.strftime("%Y%m%d"), "%Y%m%d") + timedelta(days=1)
            expire_seconds = (next_day - current_time).seconds
            r_redis.set("{}_contract".format(variety_en), str(list(all_contract)), ex=expire_seconds)
            contracts = list(all_contract)
        else:
            contracts = eval(contracts)
    return {"message": "查询成功!", "contracts": contracts}


@variety_router.post('/variety/intro/')  # 创建一个品种的介绍文件
async def create_variety_introduction(intro_file: UploadFile = Form(...),
                                      variety_en: str = Form(...),
                                      variety_name: str = Form(..., max_length=10)):
    # 将上传的文件保存
    name_text = variety_en
    # 根据品种名称和当前的时间戳生成保存的文件名称
    filename = '{}{}.pdf'.format(name_text, str(int(datetime.now().timestamp())))
    save_path = os.path.join(FILE_STORAGE, 'VARIETY/Intro/{}'.format(filename))
    sql_path = 'VARIETY/Intro/{}'.format(filename)
    # 保存到数据库并保存文件
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT variety_en,filepath FROM basic_variety_file WHERE `variety_en`=%s;",
            (variety_en,)
        )
        file_obj = cursor.fetchone()
        now_timestamp = int(datetime.now().timestamp())
        if not file_obj:
            # 新增并保存文件
            cursor.execute(
                "INSERT INTO basic_variety_file (create_time,update_time,variety_name,variety_en,filepath) "
                "VALUES (%s,%s,%s,%s,%s);",
                (now_timestamp, now_timestamp, variety_name, variety_en, sql_path)
            )
        else:
            cursor.execute(
                "UPDATE basic_variety_file SET update_time=%s,filepath=%s,variety_name=%s "
                "WHERE variety_en=%s;", (now_timestamp, sql_path, variety_name, variety_en)
            )
            # 更新数据库后删除旧文件并保存新文件
            old_filepath = os.path.join(FILE_STORAGE, file_obj['filepath'])
            if os.path.exists(old_filepath) and os.path.isfile(old_filepath):
                os.remove(old_filepath)
        # 保存文件
        file_content = await intro_file.read()
        with open(save_path, "wb") as fp:
            fp.write(file_content)
        await intro_file.close()
    return {'message': '保存品种介绍文件成功!'}


@variety_router.get('/variety/intro/')  # 获取当前系统中已有的品种介绍信息
async def get_variety_introduction():
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id,variety_name,variety_en,filepath FROM basic_variety_file "
            "WHERE variety_en<>'0' ORDER BY variety_en DESC;"
        )
        intros = cursor.fetchall()

    return {'message': '查询成功!', 'intros': intros}


@variety_router.post('/variety/rule/')  # 创建一个制度规则文件
async def create_variety_rule(rule_file: UploadFile = Form(...), rule_name: str = Form(...)):
    # 将上传的文件保存
    # 根据当前的时间戳生成保存的文件名称
    filename = '{}{}.pdf'.format(rule_name, str(int(datetime.now().timestamp())))
    save_path = os.path.join(FILE_STORAGE, 'VARIETY/Rule/{}'.format(filename))
    sql_path = 'VARIETY/Rule/{}'.format(filename)
    # 保存到数据库并保存文件
    with MySqlZ() as cursor:
        now_timestamp = int(datetime.now().timestamp())
        # 新增并保存文件
        cursor.execute(
            "INSERT INTO basic_variety_file (create_time,update_time,variety_name,variety_en,filepath) "
            "VALUES (%s,%s,%s,%s,%s);",
            (now_timestamp, now_timestamp, rule_name, '0', sql_path)
        )
        # 保存文件
        file_content = await rule_file.read()
        with open(save_path, "wb") as fp:
            fp.write(file_content)
        await rule_file.close()
    return {'message': '保存制度规则文件成功!'}


@variety_router.get('/variety/rule/')  # 获取所有的制度规则文件
async def get_variety_rule():
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id,variety_name,variety_en,filepath FROM basic_variety_file "
            "WHERE variety_en='0' ORDER BY variety_en DESC;"
        )
        rules = cursor.fetchall()

    return {'message': '查询成功!', 'rules': rules}
