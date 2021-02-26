# _*_ coding:utf-8 _*_
# @File  : spotPriceCanDelete.py
# @Time  : 2020-09-21 11:13
# @Author: zizle

""" 品种的现货报价 """
import math
from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Query, HTTPException, Body, Depends
from fastapi.encoders import jsonable_encoder
from db.mysql_z import MySqlZ, ExchangeLibDB
from db.redis_z import RedisZ
from utils.constant import VARIETY_ZH, SPOT_VARIETY_ZH
from .models import SpotPriceItem, ModifySpotItem


spot_price_router = APIRouter()


async def verify_date(date: str = Query(...)):
    try:
        date = datetime.strptime(date, "%Y%m%d")
    except Exception:
        # 直接抛出异常即可
        raise HTTPException(status_code=400, detail="the query param `date` got an error format! must be `%Y-%m-%d`.")
    return int(date.timestamp())


@spot_price_router.get('/spot-variety/', summary="所有现货品种")
async def spot_variety_all():
    # 获取redis中存储的品种
    with RedisZ() as r_redis:
        varieties = r_redis.get("spot_variety")
        if not varieties:  # 没有获取到品种
            # 查询所有品种数据
            with ExchangeLibDB() as m_cursor:
                m_cursor.execute(
                    "SELECT variety_en FROM zero_spot_price WHERE "
                    "`date`=(SELECT MAX(`date`) FROM zero_spot_price) "
                    "GROUP BY variety_en;"
                )
                query_all = m_cursor.fetchall()
            # 处理名称
            varieties = []
            for query_item in query_all:
                varieties.append(
                    (query_item["variety_en"], SPOT_VARIETY_ZH.get(query_item["variety_en"], query_item["variety_en"]))
                )
            # 将数据存入redis
            current_time = datetime.now()
            next_day = datetime.strptime(current_time.strftime("%Y%m%d"), "%Y%m%d") + timedelta(days=1)
            expire_seconds = (next_day - current_time).seconds
            r_redis.set("spot_variety", str(varieties), ex=expire_seconds)
        else:
            varieties = eval(varieties)
    return {"message": "查询成功!", "varieties": varieties}


@spot_price_router.post("/spot-price/", summary="上传现货价格数据")
async def spot_price(sources: List[SpotPriceItem] = Body(...), current_date: str = Depends(verify_date)):
    data_json = jsonable_encoder(sources)
    with ExchangeLibDB() as cursor:
        # 获取今日之前最新的现货价格数据
        cursor.execute(
            "SELECT * FROM zero_spot_price WHERE `date`=(SELECT MAX(`date`) FROM zero_spot_price);"
        )
        pre_spots = cursor.fetchall()
        # 转为dict
        pre_spots_dict = {item['variety_en']: item['price'] for item in pre_spots}
        for spot_item in data_json:
            pre_price = pre_spots_dict.get(spot_item['variety_en'])
            if pre_price:
                spot_item['increase'] = round(float(spot_item['price'] - float(pre_price)), 4)
            else:
                spot_item['increase'] = spot_item['price']
        count = cursor.executemany(
            "INSERT IGNORE INTO `zero_spot_price` "
            "(`date`,`variety_en`,`price`,`increase`) "
            "VALUES (%(date)s,%(variety_en)s,%(price)s,%(increase)s);",
            data_json
        )
        message = "保存{}现货价格数据成功!\n新增数量:{}".format(current_date, count)
    return {"message": message}


@spot_price_router.post("/spot-price/update/", summary="更新或增加现货价格数据")
async def update_spot_price():
    
    return {'message': '保存成功!'}


@spot_price_router.get("/spot-price/", summary="获取某日现货价格数据")
async def query_spot_price(query_date: int = Depends(verify_date)):
    with ExchangeLibDB() as cursor:
        cursor.execute(
           "SELECT id,`date`,variety_en,price,increase "
           "FROM zero_spot_price "
           "WHERE `date`=%s;",
           (query_date, )
        )
        data = cursor.fetchall()

    for spot_item in data:
        spot_item["variety_zh"] = VARIETY_ZH.get(spot_item["variety_en"], spot_item["variety_en"])
        spot_item["date"] = datetime.fromtimestamp(spot_item['date']).strftime('%Y-%m-%d')
        spot_item["price"] = int(spot_item['price']) if round(math.modf(spot_item['price'])[0], 4) == 0 else float(spot_item['price'])
        spot_item["increase"] = int(spot_item['increase']) if round(math.modf(spot_item['increase'])[0], 4) == 0 else float(spot_item['increase'])
    return {"message": "获取{}现货价格数据成功!".format(datetime.fromtimestamp(query_date).strftime('%Y-%m-%d')), "data": data}


@spot_price_router.put("/spot-price/{record_id}/", summary="修改某个现货价格记录")
async def modify_spot_price(record_id: int, spot_item: ModifySpotItem = Body(...)):
    with ExchangeLibDB() as cursor:
        cursor.execute(
            "UPDATE zero_spot_price SET "
            "price=%(price)s,increase=%(increase)s "
            "WHERE `id`=%(id)s and variety_en=%(variety_en)s;",
            jsonable_encoder(spot_item)
        )
    return {"message": "修改ID = {}的现货数据成功!".format(record_id)}


@spot_price_router.get("/latest-spotprice/", summary="首页即时现货报价")
def get_latest_spot_price(count: int = Query(5, ge=5, le=50)):
    with ExchangeLibDB() as cursor:
        cursor.execute(
            "SELECT id,`date`,variety_en,price,increase "
            "FROM zero_spot_price "
            "WHERE `date`=(SELECT MAX(date) FROM zero_spot_price) "
            "ORDER BY id DESC LIMIT %s;",
            (count, )
        )
        sport_prices = cursor.fetchall()
    for spot_item in sport_prices:
        spot_item["variety_zh"] = VARIETY_ZH.get(spot_item["variety_en"], spot_item["variety_en"])
        spot_item["date"] = datetime.fromtimestamp(spot_item['date']).strftime('%Y-%m-%d')
        spot_item["price"] = int(spot_item['price']) if round(math.modf(spot_item['price'])[0], 4) == 0 else float(spot_item['price'])
        spot_item["increase"] = int(spot_item['increase']) if round(math.modf(spot_item['increase'])[0], 4) == 0 else float(spot_item['increase'])
        # 兼容旧版首页(客户端<1.4.7)
        spot_item["spot_price"] = spot_item["price"]
        spot_item["price_increase"] = spot_item["increase"]
    return {"message": "获取指定数量现货报价成功!", "sport_prices": sport_prices}
