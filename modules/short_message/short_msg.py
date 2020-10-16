# _*_ coding:utf-8 _*_
# @File  : short_msg.py
# @Time  : 2020-09-16 09:45
# @Author: zizle
""" 短信通接口
API-1: 短信通的上传保存(未使用)
API-2: 根据起始时间查询今日短信通
API-3: 删除一条短信通
API-4: 修改一条短信通
API-5: 获取最新的x条短信通
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException, Body
from utils.verify import decipher_user_token, oauth2_scheme
from db.mysql_z import MySqlZ

shortmsg_router = APIRouter()


def verify_datetime(start_time: str = Query(...)):
    """ 验证日期时间 """
    try:
        current_datetime = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S")
    except Exception:
        current_datetime = datetime.now()
    return current_datetime


@shortmsg_router.post("/short-message/", summary="上传短信通")
async def save_short_message():
    return {"该API待开发"}


@shortmsg_router.get("/short-message/", summary="获取短信通信息")
async def get_short_message(
        start_time: datetime = Depends(verify_datetime)
):
    end_time = start_time + timedelta(days=1)
    end_time = end_time.strftime("%Y-%m-%dT00:00:00")
    start_time = start_time.strftime("%Y-%m-%dT%H:%M:%S")
    # 查询数据
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id, DATE_FORMAT(create_time,'%%Y-%%m-%%dT%%H:%%i:%%S') AS create_time,"
            "DATE_FORMAT(create_time,'%%H:%%i') AS time_str,"
            "creator,content "
            "FROM short_message "
            "WHERE DATE_FORMAT(create_time, '%%Y-%%m-%%dT%%H:%%i:%%S') > %s AND "
            "DATE_FORMAT(create_time, '%%Y-%%m-%%dT%%H:%%i:%%S') < %s "
            "ORDER BY create_time ASC;",
            (start_time, end_time)
        )
        short_messages = cursor.fetchall()
    content_model = "<div style='text-indent:30px;line-height:25px;font-size:13px;'>" \
                    "<span style='font-size:15px;font-weight:bold;color:rgb(233,20,20);'>{}</span>" \
                    "{}</div>"
    for msg_item in short_messages:
        msg_item["content"] = content_model.format(msg_item["time_str"], msg_item["content"])
    return {"message": "查询成功", "short_messages": short_messages}


@shortmsg_router.delete("/short-message/{msg_id}/", summary="删除一条短信通")
async def delete_short_message(msg_id: int, user_token: str = Depends(oauth2_scheme)):
    # 验证操作的人身份,删除或不删除id=msg_id的短信通
    user_id,  _ = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unknown User")
    with MySqlZ() as cursor:
        # 删除短信通(先尝试删除自己发的短信通)
        effect_row = cursor.execute(
            "DELETE FROM short_message WHERE id=%s AND creator=%s;", (msg_id, user_id)
        )
        if effect_row == 0:  # 表示这条并非自己发的
            cursor.execute(
                "SELECT id,role FROM user_user WHERE id=%s;", (user_id, )
            )
            user_info = cursor.fetchone()
            if not user_info or user_info["role"] not in ["operator", "superuser"]:
                raise HTTPException(status_code=401, detail="UnAuthenticated")
            cursor.execute(
                "DELETE FROM short_message WHERE id=%s;", (msg_id, )
            )
    return {"message": "操作完成!"}


@shortmsg_router.put("/short-message/{msg_id}/", summary="修改一条短信通")
async def modify_short_message(
        msg_id: int,
        message_content: str = Body(..., embed=True),
        user_token: str = Depends(oauth2_scheme),
):
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unknown User")
    with MySqlZ() as cursor:
        # 修改短信通(先尝试修改自己发的短信通)
        effect_row = cursor.execute(
            "UPDATE short_message SET content=%s WHERE id=%s AND creator=%s;",
            (message_content, msg_id, user_id)
        )
        if effect_row == 0:  # 表示这条并非自己发的
            cursor.execute(
                "SELECT id,role FROM user_user WHERE id=%s;", (user_id, )
            )
            user_info = cursor.fetchone()
            if not user_info or user_info["role"] not in ["operator", "superuser"]:
                raise HTTPException(status_code=401, detail="UnAuthenticated")
            cursor.execute(
                "UPDATE short_message SET content=%s WHERE id=%s;", (message_content, msg_id, )
            )
    return {"message": "操作完成!"}


@shortmsg_router.get("/instant-message/", summary="获取最新的x条短信通信息")
async def get_instant_message(count: int = Query(5, ge=1, le=50)):
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id, DATE_FORMAT(create_time,'%%Y-%%m-%%dT%%H:%%i:%%S') AS create_time,"
            "DATE_FORMAT(create_time,'%%H:%%i') AS time_str,"
            "creator,content "
            "FROM short_message "
            "ORDER BY id DESC LIMIT %s;",
            (count, )
        )
        short_messages = cursor.fetchall()
    return {"message": "获取最新短信通成功!", "short_messages": short_messages}