# _*_ coding:utf-8 _*_
# @File  : updating.py
# @Time  : 2020-08-03 8:20
# @Author: zizle
import os
import json
from enum import Enum
from fastapi import APIRouter, Query, HTTPException
from configs import APP_DIR

updating_router = APIRouter()


class SysBitEnum(str, Enum):
    big: str = "64"
    small: str = "32"


@updating_router.get("/check_version/", summary="版本检查")
async def check_version(
        version: str = Query(...),
        plateform: str = Query(...),
        sys_bit: SysBitEnum = Query(...),
        is_manager: int = Query(0, ge=0, le=1)
):
    if plateform not in ["WIN7", "WIN10"]:
        raise HTTPException(status_code=400, detail="plateform error.")

    client_type = "INSIDE" if is_manager else "OUTSIDE"
    # 读取当前请求得系统版本
    json_path = os.path.join(APP_DIR, 'conf/update{}_{}_{}.json'.format(client_type, plateform, sys_bit.value))
    with open(json_path, "r", encoding="utf-8") as conf:
        update_json = json.load(conf)
    lasted_version = update_json["VERSION"]
    if version != lasted_version:
        update_files = update_json["FILES"]
        update_needed = True
        update_detail = update_json["UPDATE"]
    else:
        update_files = dict()
        update_needed = False
        lasted_version = "已是最新"
        update_detail = "<p>已是最新</p>"
    return {
        "message": "版本更新查询成功!",
        "update_files": update_files,
        "update_needed": update_needed,
        "last_version": lasted_version,
        "file_server": update_json["SERVER"],
        "update_detail": update_detail
    }
