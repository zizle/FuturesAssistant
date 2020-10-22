# _*_ coding:utf-8 _*_
# @File  : saver.py
# @Time  : 2020-07-23 21:40
# @Author: zizle
from typing import List
from datetime import datetime
from fastapi import APIRouter, Body, HTTPException, Depends, Query
from fastapi.encoders import jsonable_encoder
from db.mysql_z import ExchangeLibDB
from .validate_items import (CZCEDailyItem, CZCERankItem, CZCEReceiptItem, SHFEDailyItem, SHFERankItem, SHFEReceiptItem,
                             CFFEXDailyItem, CFFEXRankItem, DCEDailyItem, DCERankItem, DCEReceiptItem)

saver_router = APIRouter()


async def verify_date(date: str = Query(...)):
    try:
        date = datetime.strptime(date, "%Y-%m-%d")
    except Exception:
        # 直接抛出异常即可
        raise HTTPException(status_code=400, detail="the query param `date` got an error format! must be `%Y-%m-%d`.")
    return date.strftime("%Y%m%d")


@saver_router.post("/exchange/czce/daily/", summary="保存郑商所日交易数据")
async def save_czce_daily(
        sources: List[CZCEDailyItem] = Body(...),
        current_date: str = Depends(verify_date)
):
    data_json = jsonable_encoder(sources)
    save_sql = "INSERT INTO `czce_daily` " \
               "(`date`,`variety_en`,`contract`,`open_price`,`highest`,`lowest`,`close_price`," \
               "`settlement`,`zd_1`,`zd_2`,`trade_volume`,`empty_volume`,`pre_settlement`," \
               "`increase_volume`,`trade_price`,`delivery_price`) " \
               "VALUES (%(date)s,%(variety_en)s,%(contract)s,%(open_price)s,%(highest)s,%(lowest)s,%(close_price)s," \
               "%(settlement)s,%(zd_1)s,%(zd_2)s,%(trade_volume)s,%(empty_volume)s,%(pre_settlement)s," \
               "%(increase_volume)s,%(trade_price)s,%(delivery_price)s);"
    with ExchangeLibDB() as cursor:
        # 查询数据时间
        cursor.execute("SELECT `id`, `date` FROM `czce_daily` WHERE `date`=%s;" % current_date)
        fetch_one = cursor.fetchone()
        message = "{}郑商所日交易数据已经存在,请不要重复保存!".format(current_date)
        if not fetch_one:
            count = cursor.executemany(save_sql, data_json)
            message = "保存{}郑商所日交易数据成功!\n新增数量:{}".format(current_date, count)
    return {"message": message}


@saver_router.post("/exchange/czce/rank/", summary="保存郑商所日持仓排名数据")
async def save_czce_rank(
        sources: List[CZCERankItem] = Body(...),
        current_date: str = Depends(verify_date)
):
    data_json = jsonable_encoder(sources)

    save_sql = "INSERT INTO `czce_rank` " \
               "(`date`,`variety_en`,`contract`,`rank`," \
               "`trade_company`,`trade`,`trade_increase`," \
               "`long_position_company`,`long_position`,`long_position_increase`," \
               "`short_position_company`,`short_position`,`short_position_increase`) " \
               "VALUES (%(date)s,%(variety_en)s,%(contract)s,%(rank)s," \
               "%(trade_company)s,%(trade)s,%(trade_increase)s," \
               "%(long_position_company)s,%(long_position)s,%(long_position_increase)s," \
               "%(short_position_company)s,%(short_position)s,%(short_position_increase)s);"
    with ExchangeLibDB() as cursor:
        # 查询数据时间
        cursor.execute("SELECT `id`, `date` FROM `czce_rank` WHERE `date`=%s;" % current_date)
        fetch_one = cursor.fetchone()
        message = "{}郑商所日持仓排名数据已经存在,请不要重复保存!".format(current_date)
        if not fetch_one:
            count = cursor.executemany(save_sql, data_json)
            message = "保存{}郑商所日持仓排名数据成功!\n新增数量:{}".format(current_date, count)
    return {"message": message}


@saver_router.post("/exchange/czce/receipt/", summary="保存郑商所仓单日报数据")
async def save_czce_receipt(
        sources: List[CZCEReceiptItem] = Body(...),
        current_date: str = Depends(verify_date)
):
    data_json = jsonable_encoder(sources)
    save_sql = "INSERT INTO `czce_receipt` " \
               "(`date`,`variety_en`,`warehouse`," \
               "`receipt`,`receipt_increase`,`premium_discount`) " \
               "VALUES (%(date)s,%(variety_en)s,%(warehouse)s," \
               "%(receipt)s,%(receipt_increase)s,%(premium_discount)s);"
    with ExchangeLibDB() as cursor:
        # 查询数据时间
        cursor.execute("SELECT `id`, `date` FROM `czce_receipt` WHERE `date`=%s;" % current_date)
        fetch_one = cursor.fetchone()
        message = "{}郑商所仓单日报数据已经存在,请不要重复保存!".format(current_date)
        if not fetch_one:
            count = cursor.executemany(save_sql, data_json)
            message = "保存{}郑商所仓单日报数据成功!\n新增数量:{}".format(current_date, count)
    return {"message": message}


@saver_router.post("/exchange/shfe/daily/", summary="保存上期所日交易数据")
async def save_shfe_daily(
        sources: List[SHFEDailyItem] = Body(...),
        current_date: str = Depends(verify_date)
):
    data_json = jsonable_encoder(sources)

    save_sql = "INSERT INTO `shfe_daily` " \
               "(`date`,`variety_en`,`contract`," \
               "`open_price`,`highest`,`lowest`,`close_price`,`settlement`,`zd_1`,`zd_2`," \
               "`trade_volume`,`empty_volume`,`pre_settlement`,`increase_volume`) " \
               "VALUES (%(date)s,%(variety_en)s,%(contract)s," \
               "%(open_price)s,%(highest)s,%(lowest)s,%(close_price)s,%(settlement)s,%(zd_1)s,%(zd_2)s," \
               "%(trade_volume)s,%(empty_volume)s,%(pre_settlement)s,%(increase_volume)s);"
    with ExchangeLibDB() as cursor:
        # 查询数据时间
        cursor.execute("SELECT `id`, `date` FROM `shfe_daily` WHERE `date`=%s;" % current_date)
        fetch_one = cursor.fetchone()
        message = "{}上期所日交易数据已经存在,请不要重复保存!".format(current_date)
        if not fetch_one:
            count = cursor.executemany(save_sql, data_json)
            message = "保存{}上期所日交易数据成功!\n新增数量:{}".format(current_date, count)
    return {"message": message}


@saver_router.post("/exchange/shfe/rank/", summary="保存上期所日持仓排名数据")
async def save_shfe_rank(
        sources: List[SHFERankItem] = Body(...),
        current_date: str = Depends(verify_date)
):
    data_json = jsonable_encoder(sources)

    save_sql = "INSERT INTO `shfe_rank` " \
               "(`date`,`variety_en`,`contract`,`rank`," \
               "`trade_company`,`trade`,`trade_increase`," \
               "`long_position_company`,`long_position`,`long_position_increase`," \
               "`short_position_company`,`short_position`,`short_position_increase`) " \
               "VALUES (%(date)s,%(variety_en)s,%(contract)s,%(rank)s," \
               "%(trade_company)s,%(trade)s,%(trade_increase)s," \
               "%(long_position_company)s,%(long_position)s,%(long_position_increase)s," \
               "%(short_position_company)s,%(short_position)s,%(short_position_increase)s);"
    with ExchangeLibDB() as cursor:
        # 查询数据时间
        cursor.execute("SELECT `id`, `date` FROM `shfe_rank` WHERE `date`=%s;" % current_date)
        fetch_one = cursor.fetchone()
        message = "{}上期所日持仓排名数据已经存在,请不要重复保存!".format(current_date)
        if not fetch_one:
            count = cursor.executemany(save_sql, data_json)
            message = "保存{}上期所日持仓排名数据成功!\n新增数量:{}".format(current_date, count)
    return {"message": message}


@saver_router.post("/exchange/shfe/receipt/", summary="保存上期所所仓单日报数据")
async def save_shfe_receipt(
        sources: List[SHFEReceiptItem] = Body(...),
        current_date: str = Depends(verify_date)
):
    data_json = jsonable_encoder(sources)
    save_sql = "INSERT INTO `shfe_receipt` " \
               "(`date`,`variety_en`,`warehouse`," \
               "`receipt`,`receipt_increase`) " \
               "VALUES (%(date)s,%(variety_en)s,%(warehouse)s," \
               "%(receipt)s,%(receipt_increase)s);"

    with ExchangeLibDB() as cursor:
        # 查询数据时间
        cursor.execute("SELECT `id`, `date` FROM `shfe_receipt` WHERE `date`=%s;" % current_date)
        fetch_one = cursor.fetchone()
        message = "{}上期所仓单日报数据已经存在,请不要重复保存!".format(current_date)
        if not fetch_one:
            count = cursor.executemany(save_sql, data_json)
            message = "保存{}上期所仓单日报数据成功!\n新增数量:{}".format(current_date, count)
    return {"message": message}


@saver_router.post("/exchange/cffex/daily/", summary="保存中金所日交易数据")
async def save_cffex_daily(
        sources: List[CFFEXDailyItem] = Body(...),
        current_date: str = Depends(verify_date)
):
    data_json = jsonable_encoder(sources)

    save_sql = "INSERT INTO `cffex_daily` " \
               "(`date`,`variety_en`,`contract`,`open_price`,`highest`,`lowest`," \
               "`close_price`,`settlement`,`zd_1`,`zd_2`,`trade_volume`,`empty_volume`,`trade_price`) " \
               "VALUES (%(date)s,%(variety_en)s,%(contract)s,%(open_price)s,%(highest)s,%(lowest)s," \
               "%(close_price)s,%(settlement)s,%(zd_1)s,%(zd_2)s,%(trade_volume)s,%(empty_volume)s,%(trade_price)s);"
    with ExchangeLibDB() as cursor:
        # 查询数据时间
        cursor.execute("SELECT `id`, `date` FROM `cffex_daily` WHERE `date`=%s;" % current_date)
        fetch_one = cursor.fetchone()
        message = "{}中金所日交易数据已经存在,请不要重复保存!".format(current_date)
        if not fetch_one:
            count = cursor.executemany(save_sql, data_json)
            message = "保存{}中金所日交易数据成功!\n新增数量:{}".format(current_date, count)
    return {"message": message}


@saver_router.post("/exchange/cffex/rank/", summary="保存中金所日持仓排名数据")
async def save_cffex_rank(
        sources: List[CFFEXRankItem] = Body(...),
        current_date: str = Depends(verify_date)
):
    data_json = jsonable_encoder(sources)

    save_sql = "INSERT INTO `cffex_rank` " \
               "(`date`,`variety_en`,`contract`,`rank`," \
               "`trade_company`,`trade`,`trade_increase`," \
               "`long_position_company`,`long_position`,`long_position_increase`," \
               "`short_position_company`,`short_position`,`short_position_increase`) " \
               "VALUES (%(date)s,%(variety_en)s,%(contract)s,%(rank)s," \
               "%(trade_company)s,%(trade)s,%(trade_increase)s," \
               "%(long_position_company)s,%(long_position)s,%(long_position_increase)s," \
               "%(short_position_company)s,%(short_position)s,%(short_position_increase)s);"
    with ExchangeLibDB() as cursor:
        # 查询数据时间
        cursor.execute("SELECT `id`, `date` FROM `cffex_rank` WHERE `date`=%s;" % current_date)
        fetch_one = cursor.fetchone()
        message = "{}中金所日持仓排名数据已经存在,请不要重复保存!".format(current_date)
        if not fetch_one:
            count = cursor.executemany(save_sql, data_json)
            message = "保存{}中金所日持仓排名数据成功!\n新增数量:{}".format(current_date, count)
    return {"message": message}


@saver_router.post("/exchange/dce/daily/", summary="保存大商所日交易数据")
async def save_dce_daily(
        sources: List[DCEDailyItem] = Body(...),
        current_date: str = Depends(verify_date)
):
    data_json = jsonable_encoder(sources)

    save_sql = "INSERT INTO `dce_daily` " \
               "(`date`,`variety_en`,`contract`," \
               "`open_price`,`highest`,`lowest`,`close_price`," \
               "`settlement`,`zd_1`,`zd_2`,`trade_volume`,`empty_volume`," \
               "`pre_settlement`,`increase_volume`,`trade_price`) " \
               "VALUES (%(date)s,%(variety_en)s,%(contract)s," \
               "%(open_price)s,%(highest)s,%(lowest)s,%(close_price)s," \
               "%(settlement)s,%(zd_1)s,%(zd_2)s,%(trade_volume)s,%(empty_volume)s," \
               "%(pre_settlement)s,%(increase_volume)s,%(trade_price)s);"
    with ExchangeLibDB() as cursor:
        # 查询数据时间
        cursor.execute("SELECT `id`, `date` FROM `dce_daily` WHERE `date`=%s;" % current_date)
        fetch_one = cursor.fetchone()
        message = "{}大商所日交易数据已经存在,请不要重复保存!".format(current_date)
        if not fetch_one:
            count = cursor.executemany(save_sql, data_json)
            message = "保存{}大商所日交易数据成功!\n新增数量:{}".format(current_date, count)
    return {"message": message}


@saver_router.post("/exchange/dce/rank/", summary="保存大商所所日持仓排名数据")
async def save_dce_rank(
        sources: List[DCERankItem] = Body(...),
        current_date: str = Depends(verify_date)
):
    data_json = jsonable_encoder(sources)
    save_sql = "INSERT INTO `dce_rank` " \
               "(`date`,`variety_en`,`contract`,`rank`," \
               "`trade_company`,`trade`,`trade_increase`," \
               "`long_position_company`,`long_position`,`long_position_increase`," \
               "`short_position_company`,`short_position`,`short_position_increase`) " \
               "VALUES (%(date)s,%(variety_en)s,%(contract)s,%(rank)s," \
               "%(trade_company)s,%(trade)s,%(trade_increase)s," \
               "%(long_position_company)s,%(long_position)s,%(long_position_increase)s," \
               "%(short_position_company)s,%(short_position)s,%(short_position_increase)s);"
    with ExchangeLibDB() as cursor:
        # 查询数据时间
        cursor.execute("SELECT `id`, `date` FROM `dce_rank` WHERE `date`=%s;" % current_date)
        fetch_one = cursor.fetchone()
        message = "{}大商所日持仓排名数据已经存在,请不要重复保存!".format(current_date)
        if not fetch_one:
            count = cursor.executemany(save_sql, data_json)
            message = "保存{}大商所日持仓排名数据成功!\n新增数量:{}".format(current_date, count)
    return {"message": message}


@saver_router.post("/exchange/dce/receipt/", summary="保存大商所所仓单日报数据")
async def save_dce_receipt(
        sources: List[DCEReceiptItem] = Body(...),
        current_date: str = Depends(verify_date)
):
    data_json = jsonable_encoder(sources)
    save_sql = "INSERT INTO `dce_receipt` " \
               "(`date`,`variety_en`,`warehouse`," \
               "`receipt`,`receipt_increase`) " \
               "VALUES (%(date)s,%(variety_en)s,%(warehouse)s," \
               "%(receipt)s,%(receipt_increase)s);"

    with ExchangeLibDB() as cursor:
        # 查询数据时间
        cursor.execute("SELECT `id`, `date` FROM `dce_receipt` WHERE `date`=%s;" % current_date)
        fetch_one = cursor.fetchone()
        message = "{}大商所仓单日报数据已经存在,请不要重复保存!".format(current_date)
        if not fetch_one:
            count = cursor.executemany(save_sql, data_json)
            message = "保存{}大商所仓单日报数据成功!\n新增数量:{}".format(current_date, count)
    return {"message": message}
