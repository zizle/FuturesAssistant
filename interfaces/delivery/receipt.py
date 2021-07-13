# _*_ coding:utf-8 _*_
# @File  : receipt.py
# @Time  : 2020-09-24 13:26
# @Author: zizle
""" 仓库仓单数据
API-1: 仓单数据保存
"""
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, Body, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from utils.verify import oauth2_scheme, decipher_user_token
from db.mysql_z import MySqlZ
from .models import ReceiptItem
receipt_router = APIRouter()


def verify_date(today: str = Query(...)):
    try:
        datetime.strptime(today, "%Y%m%d")
    except Exception:
        raise HTTPException(status_code=400, detail="Param today format: %Y%m%d")
    return today


@receipt_router.post("/delivery/receipt/", summary="保存仓单数据", status_code=201)
async def save_delivery_receipt(
        user_token: str = Depends(oauth2_scheme),
        receipt_item: List[ReceiptItem] = Body(...)
):
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="UnAuthorization")
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id, role FROM user_user WHERE id=%s;", (user_id, )
        )
        user_role = cursor.fetchone()
        if not user_role or user_role["role"] not in ["superuser", "operator"]:
            raise HTTPException(status_code=401, detail="UnAuthorization")
        # 查询今日仓单是否已经存在,存在则不添加
        today = receipt_item[0].date
        cursor.execute("SELECT `date` FROM delivery_warehouse_receipt WHERE `date`=%s;", (today, ))
        if cursor.fetchone():
            raise HTTPException(status_code=403, detail="Today Receipts Exist.")
        # 保存数据到数据库
        save_count = cursor.executemany(
            "INSERT INTO delivery_warehouse_receipt (warehouse_code,warehouse_name,variety,"
            "variety_en,`date`,receipt,increase) VALUES (%(warehouse_code)s,%(warehouse_name)s,%(variety)s,"
            "%(variety_en)s,%(date)s,%(receipt)s,%(increase)s);",
            jsonable_encoder(receipt_item)
        )
    return {"message": "保存成功!", "save_count": save_count}