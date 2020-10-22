# _*_ coding:utf-8 _*_
# @File  : spot_price.py
# @Time  : 2020-09-21 11:13
# @Author: zizle

""" 品种的现货报价 """
from typing import List
from datetime import datetime
from fastapi import APIRouter, Query, HTTPException, Body, Depends
from fastapi.encoders import jsonable_encoder
from db.mysql_z import MySqlZ
from utils.constant import VARIETY_ZH
from .models import SpotPriceItem, ModifySpotItem


spot_price_router = APIRouter()


async def verify_date(date: str = Query(...)):
    try:
        date = datetime.strptime(date, "%Y%m%d")
    except Exception:
        # 直接抛出异常即可
        raise HTTPException(status_code=400, detail="the query param `date` got an error format! must be `%Y-%m-%d`.")
    return date.strftime("%Y%m%d")


@spot_price_router.post("/spot-price/", summary="上传现货价格数据")
async def spot_price(sources: List[SpotPriceItem] = Body(...), current_date: str = Depends(verify_date)):
    data_json = jsonable_encoder(sources)
    save_sql = "INSERT INTO `industry_spot_price` " \
               "(`date`,`variety_en`,`spot_price`,`price_increase`) " \
               "VALUES (%(date)s,%(variety_en)s,%(spot_price)s,%(price_increase)s);"
    with MySqlZ() as cursor:
        # 查询数据时间
        cursor.execute("SELECT `id`, `date` FROM `industry_spot_price` WHERE `date`=%s;" % current_date)
        fetch_one = cursor.fetchone()
        message = "{}现货价格数据已经存在,请不要重复保存!".format(current_date)
        if not fetch_one:
            count = cursor.executemany(save_sql, data_json)
            message = "保存{}现货价格数据成功!\n新增数量:{}".format(current_date, count)
    return {"message": message}


@spot_price_router.get("/spot-price/", summary="获取某日现货价格数据")
async def query_spot_price(query_date: str = Depends(verify_date)):
    with MySqlZ() as cursor:
        cursor.execute(
           "SELECT id,`date`,variety_en,spot_price,price_increase "
           "FROM industry_spot_price "
           "WHERE `date`=%s;",
           (query_date, )
        )
        data = cursor.fetchall()

    for spot_item in data:
        spot_item["variety_zh"] = VARIETY_ZH.get(spot_item["variety_en"], spot_item["variety_en"])
        spot_item["spot_price"] = int(spot_item["spot_price"])
        spot_item["price_increase"] = int(spot_item["price_increase"])
        spot_item["date"] = datetime.strptime(spot_item["date"], "%Y%m%d").strftime("%Y-%m-%d")
    return {"message": "获取{}现货价格数据成功!".format(query_date), "data": data}


@spot_price_router.put("/spot-price/{record_id}/", summary="修改某个现货价格记录")
async def modify_spot_price(record_id: int, spot_item: ModifySpotItem = Body(...)):
    with MySqlZ() as cursor:
        cursor.execute(
            "UPDATE industry_spot_price SET "
            "spot_price=%(spot_price)s,price_increase=%(price_increase)s "
            "WHERE `id`=%(id)s and variety_en=%(variety_en)s;",
            jsonable_encoder(spot_item)
        )
    return {"message": "修改ID = {}的现货数据成功!".format(record_id)}


@spot_price_router.get("/latest-spotprice/", summary="首页即时现货报价")
def get_latest_spot_price(count: int = Query(5, ge=5, le=50)):
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id,create_time,`date`,variety_en,spot_price,price_increase "
            "FROM industry_spot_price "
            "ORDER BY id DESC LIMIT %s;",
            (count, )
        )
        sport_prices = cursor.fetchall()
    for spot_item in sport_prices:
        spot_item["variety_zh"] = VARIETY_ZH.get(spot_item["variety_en"], spot_item["variety_en"])
        spot_item["spot_price"] = int(spot_item["spot_price"])
        spot_item["price_increase"] = int(spot_item["price_increase"])
        spot_item["date"] = datetime.strptime(spot_item["date"], "%Y%m%d").strftime("%m-%d")
    return {"message": "获取指定数量现货报价成功!", "sport_prices": sport_prices}
