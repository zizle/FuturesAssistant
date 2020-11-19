# _*_ coding:utf-8 _*_
# @File  : spot.py
# @Time  : 2020-11-18 13:40
# @Author: zizle
""" 现货相关接口 （部分接口在产业数据中）"""
from datetime import datetime, timedelta
from fastapi import APIRouter
from db.redis_z import RedisZ
from db.mysql_z import MySqlZ
from utils.constant import SPOT_VARIETY_ZH

spot_router = APIRouter()


@spot_router.get('/spot-variety/', summary="所有现货品种")
async def spot_variety_all():
    # 获取redis中存储的品种
    with RedisZ() as r_redis:
        varieties = r_redis.get("spot_variety")
        if not varieties:  # 没有获取到品种
            # 查询所有品种数据

            with MySqlZ() as m_cursor:
                m_cursor.execute(
                    "SELECT variety_en FROM industry_spot_price WHERE "
                    "`date`=(SELECT MAX(`date`) FROM industry_spot_price) "
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