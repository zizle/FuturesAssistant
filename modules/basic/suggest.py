# _*_ coding:utf-8 _*_
# @File  : suggest.py
# @Time  : 2021-02-22 09:40
# @Author: zizle


# 意见反馈
import datetime
from fastapi import APIRouter, Body, HTTPException
from utils.verify import decipher_user_token
from db.mysql_z import MySqlZ
from .validate_models import SuggestItem

suggest_api = APIRouter()


@suggest_api.post('/suggest/', summary='用户提交建议')  #
async def add_suggest(suggest_item: SuggestItem = Body(...)):
    # 解析用户信息，保存建议内容
    user_id, _ = decipher_user_token(suggest_item.user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail='Unknown User')
    now_ts = int(datetime.datetime.now().timestamp())
    with MySqlZ() as cursor:
        cursor.execute(
            "INSERT INTO basic_suggest (create_time,user_id,content,links) "
            "VALUES (%s,%s,%s,%s);",
            (now_ts, user_id, suggest_item.content, suggest_item.links)
        )
    return {'message': '提交成功!'}


@suggest_api.get('/suggest/', summary='获取用户的建议列表')  #
async def get_suggest():
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT bst.id,utb.username,utb.note,bst.create_time,bst.content,bst.links,bst.is_accept "
            "FROM basic_suggest AS bst "
            "INNER JOIN user_user AS utb "
            "ON bst.user_id=utb.id "
            "ORDER BY bst.create_time DESC;"
        )
        suggest_list = cursor.fetchall()

    for item in suggest_list:
        item['create_time'] = datetime.datetime.fromtimestamp(item['create_time']).strftime('%Y-%m-%d %H:%M:%S')
        if item['note']:
            item['username'] = item['username'] + '(' + item['note'] + ')'

    return {'message': '查询成功!', 'suggestions': suggest_list}
