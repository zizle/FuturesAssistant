# _*_ coding:utf-8 _*_
# @File  : warehouse.py
# @Time  : 2020-09-22 13:25
# @Author: zizle
""" 交割仓库管理
后台管理：
API-1: 交割仓库编号查询
API-2: 交割仓库编号增加
API-3: 交割仓库管理查询
API-4: 交割仓库管理新增
API-5: 交割仓库的交割品种查询
API-6: 交割仓库的交割品种增加或修改
API-7: 品种的交割信息查询
API-8: 品种的交割信息修改
前台信息：
API-1: 获取品种下的仓库信息
API-2: 获取省份下的仓库信息
API-3: 获取仓库的仓单信息
"""
import re
from fastapi import APIRouter, Body, HTTPException, Depends, Query
from fastapi.encoders import jsonable_encoder
from utils.verify import decipher_user_token, oauth2_scheme
from utils.char_reverse import strQ2B
from db.mysql_z import MySqlZ
from .models import WarehouseItem, DeliveryVarietyItem, VarietyDeliveryMsgItem

warehouse_router = APIRouter()


def verify_warehouse_fixed_code(fixed_code: str):
    """ 验证仓库的编码 """
    if re.match(r'^[0-9]{4}$', fixed_code):
        return fixed_code
    else:
        raise HTTPException(status_code=400, detail="Unknown Warehouse")


def verify_variety_en(variety_en):
    if re.match(r'^[A-Z]{1,2}$', variety_en):
        return variety_en
    else:
        raise HTTPException(status_code=400, detail="variety_en: [A-Z]{1,2}")


""" 前台信息 """


@warehouse_router.get("/{variety_en}/warehouses/", summary="品种下的所有仓库信息")
async def variety_warehouses(variety_en: str = Depends(verify_variety_en)):
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT dwtb.id,dwtb.fixed_code,dwtb.area,dwtb.name,dwtb.short_name,dwtb.addr,dwtb.arrived,"
            "dwtb.longitude,dwtb.latitude,"
            "dwvtb.variety,dwvtb.variety_en,dwvtb.linkman,dwvtb.links,dwvtb.premium,dwvtb.receipt_unit "
            "FROM delivery_warehouse AS dwtb "
            "INNER JOIN delivery_warehouse_variety AS dwvtb "
            "ON dwtb.fixed_code=dwvtb.warehouse_code AND dwvtb.variety_en=%s AND dwvtb.is_active=1;",
            (variety_en, )
        )
        warehouses = cursor.fetchall()
    return {"message": "查询成功!", "warehouses": warehouses}


@warehouse_router.get("/province-warehouse/", summary="获取指定省份下的所有仓库信息")
async def query_province_warehouse(province: str = Query(...)):
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT dwtb.id,dwtb.fixed_code,dwtb.area,dwtb.name,dwtb.short_name,dwtb.addr,dwtb.arrived,"
            "dwtb.longitude,dwtb.latitude,"
            "dwvtb.linkman,dwvtb.links,dwvtb.premium,dwvtb.receipt_unit, "
            "GROUP_CONCAT(dwvtb.variety) AS delivery_varieties "
            "FROM delivery_warehouse AS dwtb "
            "LEFT JOIN delivery_warehouse_variety AS dwvtb "
            "ON dwtb.fixed_code=dwvtb.warehouse_code AND dwvtb.is_active=1 "
            "WHERE dwtb.area=%s "
            "GROUP BY dwtb.id;",
            (province, )
        )
        warehouses = cursor.fetchall()
    return {"message": "查询成功!", "warehouses": warehouses}


@warehouse_router.get("/warehouse/{fixed_code}/receipt/", summary="获取仓库的仓单信息")
async def warehouse_receipts(
        fixed_code: str = Depends(verify_warehouse_fixed_code),
        variety_en: str = Query(0)
):
    with MySqlZ() as cursor:
        if variety_en:
            variety_en = verify_variety_en(variety_en)
        # 查询仓库[指定品种]信息和仓单
        cursor.execute(
            "SELECT dwtb.id,dwtb.fixed_code,dwtb.name,dwtb.short_name,dwtb.addr,"
            "dwvtb.variety,dwvtb.variety_en,dwvtb.linkman,dwvtb.links,dwvtb.premium,dwvtb.receipt_unit,"
            "dvmtb.last_trade,dvmtb.receipt_expire,dvmtb.delivery_unit,dvmtb.limit_holding "
            "FROM delivery_warehouse_variety AS dwvtb "
            "INNER JOIN delivery_warehouse AS dwtb "
            "ON dwvtb.warehouse_code=dwtb.fixed_code "
            "LEFT JOIN delivery_variety_message AS dvmtb "
            "ON dvmtb.variety_en=dwvtb.variety_en "
            "WHERE dwtb.fixed_code=%s AND IF(%s=0,TRUE,dwvtb.variety_en=%s);",
            (fixed_code, variety_en, variety_en)
        )
        query_result = cursor.fetchall()
        if len(query_result) <= 0:
            return {'message': '获取仓单成功', 'warehouses_receipts': {}}
        # 整理出品种列表以及品种的仓单
        response_data = dict()
        variety_receipts = list()
        # 查询仓单sql
        receipt_statement = "SELECT id,warehouse_code,warehouse_name,variety,variety_en,`date`,receipt,increase " \
                            "FROM `delivery_warehouse_receipt` " \
                            "WHERE `variety_en`=%s AND `warehouse_code`=%s " \
                            "ORDER BY `id` DESC " \
                            "LIMIT 10;"
        variety_first = query_result[0]
        response_data['warehouse'] = variety_first['name']
        response_data['short_name'] = variety_first['short_name']
        response_data['addr'] = variety_first['addr']
        response_data['varieties'] = variety_receipts
        for variety_item in query_result:
            variety_dict = dict()
            variety_dict['name'] = variety_item['variety']
            variety_dict['name_en'] = variety_item['variety_en']
            variety_dict['last_trade'] = variety_item['last_trade'] if variety_item['last_trade'] else ''
            variety_dict['receipt_expire'] = variety_item['receipt_expire'] if variety_item[
                'receipt_expire'] else ''
            variety_dict['delivery_unit'] = variety_item['delivery_unit'] if variety_item['delivery_unit'] else ''
            variety_dict['linkman'] = variety_item['linkman']
            variety_dict['links'] = variety_item['links']
            variety_dict['premium'] = variety_item['premium']
            cursor.execute(receipt_statement, (variety_item['variety_en'], variety_item['fixed_code']))
            variety_dict['receipts'] = cursor.fetchall()
            variety_dict['receipt_unit'] = variety_item['receipt_unit']
            variety_dict['limit_holding'] = variety_item['limit_holding']
            variety_receipts.append(variety_dict)
        return {'message': '获取仓单成功', 'warehouses_receipts': response_data}


""" 后台管理 """


@warehouse_router.get("/warehouse-number/", summary="查询所有交割仓库对应的编号")
async def query_warehouse_number():
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id,name,fixed_code "
            "FROM delivery_warehouse_number "
            "ORDER BY id;"
        )
        warehouses = cursor.fetchall()
    return {"message": "查询成功!", "warehouses": warehouses}


@warehouse_router.post("/warehouse-number/", summary="新增一个简称仓库")
async def create_warehouse_number(warehouse_short_name: str = Body(..., embed=True)):
    # 将简称字符转为半角
    warehouse_short_name = strQ2B(warehouse_short_name)
    # 查看当前名称是否已经存在
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT `name` FROM delivery_warehouse_number WHERE `name`=%s", (warehouse_short_name, )
        )
        is_exist = cursor.fetchone()
        if is_exist:
            return {"message": "仓库已存在,无需重复添加!", 'fixed_code': 0}

        # 生成fixed_code
        cursor.execute(
            "SELECT MAX(`id`) AS `maxid` FROM `delivery_warehouse_number`;"
        )
        max_id = cursor.fetchone()['maxid']
        fixed_code = '%04d' % (max_id + 1)
        cursor.execute(
            "INSERT INTO delivery_warehouse_number (`name`,fixed_code) "
            "VALUES (%s,%s);",
            (warehouse_short_name, fixed_code)
        )
        # 将仓单表中简称为这个的填上仓库编号
        cursor.execute(
            "UPDATE delivery_warehouse_receipt SET `warehouse_code`=%s WHERE `warehouse_name`=%s;",
            (fixed_code, warehouse_short_name)
        )
        return {'message': '保存成功!', 'fixed_code': fixed_code}


@warehouse_router.get("/warehouse/", summary="查询所有仓库信息")
async def query_warehouse():
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id,fixed_code,area,name,short_name,addr,arrived,"
            "DATE_FORMAT(create_time,'%Y-%m-%d') AS create_time,longitude,latitude "
            "FROM delivery_warehouse ORDER BY id;"
        )
        warehouses = cursor.fetchall()
    return {"message": "查询成功!", "warehouses": warehouses}


@warehouse_router.post("/warehouse/", summary="新增一个仓库信息", status_code=201)
async def create_warehouse(
        user_token: str = Depends(oauth2_scheme),
        warehouse_item: WarehouseItem = Body(...)
):
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unknown User")
    with MySqlZ() as cursor:
        # 查询编号
        cursor.execute(
            "SELECT id,fixed_code FROM delivery_warehouse_number WHERE `name`=%s;", (warehouse_item.short_name, )
        )
        fixed_code_info = cursor.fetchone()
        if not fixed_code_info:
            raise HTTPException(status_code=400, detail="请先添加仓库简称后再添加仓库...")
        fixed_code = fixed_code_info["fixed_code"]
        cursor.execute(
            "SELECT id FROM delivery_warehouse WHERE fixed_code=%s;", (fixed_code, )
        )
        exist = cursor.fetchone()
        if exist:
            raise HTTPException(status_code=400, detail="仓库已存在无需重复添加...")
        # 新增仓库信息
        warehouse_dict = jsonable_encoder(warehouse_item)
        warehouse_dict["fixed_code"] = fixed_code
        cursor.execute(
            "INSERT INTO delivery_warehouse (fixed_code,area,`name`,short_name,addr,arrived,longitude,latitude) "
            "VALUES (%(fixed_code)s,%(area)s,%(name)s,%(short_name)s,%(addr)s,%(arrived)s,%(longitude)s,%(latitude)s);",
            warehouse_dict
        )
    return {"message": "新增成功!"}


@warehouse_router.get("/warehouse/{fixed_code}/variety/", summary="查询某个交割仓库的交割品种")
async def query_warehouse_variety(fixed_code: str = Depends(verify_warehouse_fixed_code)):
    with MySqlZ() as cursor:
        # 查询仓库基本信息
        cursor.execute(
            "SELECT `name`,short_name FROM delivery_warehouse WHERE fixed_code=%s;", (fixed_code, )
        )
        warehouse_info = cursor.fetchone()
        if not warehouse_info:
            raise HTTPException(status_code=400, detail="该仓库不存在")
        # 查询仓库可交割的品种
        cursor.execute(
            "SELECT vtb.id,vtb.variety_name,vtb.variety_en,deliverytb.variety_en AS is_delivery "
            "FROM basic_variety AS vtb "
            "LEFT JOIN delivery_warehouse_variety AS deliverytb "
            "ON vtb.variety_en=deliverytb.variety_en AND deliverytb.is_active=1 "
            "AND deliverytb.warehouse_code=%s;",
            (fixed_code, )
        )
        varieties = cursor.fetchall()
    return {"message": "查询成功!", "varieties": varieties,
            "name": warehouse_info["name"],
            "short_name": warehouse_info["short_name"]
            }


@warehouse_router.post("/warehouse/{fixed_code}/variety/", summary="修改或新增仓库的可交割品种")
async def modify_warehouse_variety(
        fixed_code: str = Depends(verify_warehouse_fixed_code),
        user_token: str = Depends(oauth2_scheme),
        delivery_item: DeliveryVarietyItem = Body(...)
):
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail='Unknown User')
    if delivery_item.is_delivery not in [0, 1]:
        raise HTTPException(status_code=400, detail='Error Params: `is_delivery` must be 0 or 1')
    with MySqlZ() as cursor:
        # 查询用户角色
        cursor.execute(
            "SELECT id,role FROM user_user WHERE id=%s AND role='superuser' OR role='operator';",
            (user_id, )
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=401, detail="Operation Disabled")
        if delivery_item.is_delivery:  # 有交割(数据库无设置唯一索引,乖乖查吧)
            cursor.execute(
                "SELECT warehouse_code FROM delivery_warehouse_variety WHERE warehouse_code=%s AND variety_en=%s;",
                (fixed_code, delivery_item.variety_en)
            )
            if cursor.fetchone():  # 存在更新
                cursor.execute(
                    "UPDATE delivery_warehouse_variety SET variety=%(variety)s,variety_en=%(variety_en)s,"
                    "linkman=%(linkman)s,links=%(links)s,premium=%(premium)s,receipt_unit=%(receipt_unit)s,"
                    "is_active=1 WHERE warehouse_code=%(warehouse_code)s AND variety_en=%(variety_en)s;",
                    jsonable_encoder(delivery_item)
                )
            else:                 # 不存在新增
                cursor.execute(
                    "INSERT INTO delivery_warehouse_variety (warehouse_code,variety,variety_en,linkman,links,"
                    "premium,receipt_unit,is_active) VALUES "
                    "(%(warehouse_code)s,%(variety)s,%(variety_en)s,%(linkman)s,%(links)s,"
                    "%(premium)s,%(receipt_unit)s,1);",
                    jsonable_encoder(delivery_item)
                )
        else:  # 无交割
            cursor.execute(
                "UPDATE delivery_warehouse_variety SET is_active=0 WHERE warehouse_code=%s AND variety_en=%s;",
                (fixed_code, delivery_item.variety_en)
            )
    return {"message": "修改成功!"}


@warehouse_router.get("/delivery-message/", summary="所有品种的交割信息获取")
async def query_variety_delivery_message():
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id,variety,variety_en,last_trade,receipt_expire,delivery_unit,limit_holding "
            "FROM delivery_variety_message;"
        )
        delivery_msg = cursor.fetchall()
    return {"message": "查询成功!", "delivery_msg": delivery_msg}


@warehouse_router.put("/{variety_en}/delivery-message/", summary="修改一个品种的交割信息")
async def modify_variety_delivery_message(
        variety_en: str,
        user_token: str = Depends(oauth2_scheme),
        delivery_msg_item: VarietyDeliveryMsgItem = Body(...)
):
    if not re.match(r'^[A-Z]{1,2}$', variety_en):
        raise HTTPException(status_code=400, detail="Error Param `variety_en` [A-Z]{1,2}")
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unknown User")
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT role FROM user_user WHERE id=%s AND (role='superuser' OR role='operator');", (user_id, )
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=403, detail="Operation Denied")
        # 修改信息
        cursor.execute(
            "UPDATE delivery_variety_message SET "
            "variety=%(variety)s,variety_en=%(variety_en)s,last_trade=%(last_trade)s,"
            "receipt_expire=%(receipt_expire)s,delivery_unit=%(delivery_unit)s,limit_holding=%(limit_holding)s "
            "WHERE variety_en=%(variety_en)s;",
            jsonable_encoder(delivery_msg_item)
        )
    return {"message": "修改成功"}
