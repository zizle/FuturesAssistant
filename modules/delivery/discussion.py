# _*_ coding:utf-8 _*_
# @File  : discussion.py
# @Time  : 2020-09-23 13:09
# @Author: zizle

""" 交流与讨论
API-1: 用户提交问题
API-2: 用户回复问题
API-3: 用户获取问题列表
API-4: 用户获取自己发布的问题列表
API-5: 用户查询问题列表
API-6: 最新交流与讨论(10条)
"""
from fastapi import APIRouter, Depends, Body, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from utils.verify import decipher_user_token, oauth2_scheme
from db.mysql_z import MySqlZ
from .models import DiscussionItem

discussion_router = APIRouter()


@discussion_router.post("/delivery/discussion/", summary="用户提交问题", status_code=201)
async def create_discussion(
        user_token: str = Depends(oauth2_scheme),
        discussion_item: DiscussionItem = Body(...)
):
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="UnAuthorization User")
    # 加入数据库
    data = jsonable_encoder(discussion_item)
    data["author_id"] = user_id
    replies = list()
    with MySqlZ() as cursor:
        cursor.execute(
            "INSERT INTO delivery_discussion (author_id,content,parent_id) VALUES "
            "(%(author_id)s,%(content)s,%(parent_id)s);",
            data
        )
        if discussion_item.parent_id:
            replies = get_sub_reply(cursor, discussion_item.parent_id)
    return {"message": "操作成功!", "replies": replies}


def handle_discuss_item(reply_item):
    """ 处理讨论的内容 """
    reply_dict = dict()
    reply_dict['id'] = reply_item['id']
    if reply_item['username']:
        username = reply_item['username']
    else:
        phone = reply_item['phone']
        username = phone[:4] + '****' + phone[8:]
    reply_dict['username'] = username
    reply_dict['avatar'] = reply_item['avatar']
    reply_dict['text'] = reply_item['content']
    reply_dict['create_time'] = reply_item['create_time'].strftime('%Y-%m-%d')
    return reply_dict

def get_sub_reply(cursor, parent_id):
    """ 查询交流讨论的回复 """
    query_statement = "SELECT distb.id,distb.content,distb.create_time," \
                      "usertb.username,usertb.phone,usertb.avatar " \
                      "FROM `delivery_discussion` AS distb " \
                      "INNER JOIN `user_user` AS usertb " \
                      "ON distb.author_id=usertb.id " \
                      "WHERE distb.parent_id=%s " \
                      "ORDER BY distb.create_time DESC;"
    cursor.execute(query_statement, parent_id)
    sub_reply = cursor.fetchall()
    replies = list()
    for reply_item in sub_reply:
        reply_dict = handle_discuss_item(reply_item)
        replies.append(reply_dict)
    return replies


@discussion_router.get("/delivery/discussion/", summary="用户获取问题")
async def query_discussion(
        c_page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=20)
):
    query_page = c_page - 1  # 减1处理才能查到第一页
    # 查询当前页码下的数据
    limit_start = query_page * page_size
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT distb.id,distb.content,distb.create_time,"
            "usertb.username,usertb.phone,usertb.avatar "
            "FROM delivery_discussion AS distb "
            "INNER JOIN user_user AS usertb "
            "ON distb.author_id=usertb.id "
            "WHERE distb.parent_id=0 "
            "ORDER BY distb.create_time DESC "
            "LIMIT %s,%s;",
            (limit_start, page_size)
        )
        records_result = cursor.fetchall()
        # 查询总条数
        cursor.execute(
            "SELECT COUNT(distb.id) AS total FROM delivery_discussion AS distb "
            "INNER JOIN user_user AS usertb ON distb.author_id=usertb.id "
            "WHERE distb.parent_id=0;"
        )
        # 计算总页数
        total_count = cursor.fetchone()['total']
        total_page = int((total_count + page_size - 1) / page_size)
        response_data = list()
        for dis_item in records_result:
            dis_dict = handle_discuss_item(dis_item)
            # 查询回复
            dis_dict['replies'] = get_sub_reply(cursor, dis_item['id'])
            response_data.append(dis_dict)
    return {'message': '查询成功!', 'discussions': response_data, 'total_page': total_page}


@discussion_router.get("/delivery/discussion-own/", summary="用户获取自己提交的问题")
async def get_own_discussion(
        user_token: str = Depends(oauth2_scheme)
):
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        return {"message": "没有验证的用户", "discussions": []}
    # 查询用户自己的问题
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT distb.id,distb.content,distb.create_time,"
            "usertb.username,usertb.phone,usertb.avatar "
            "FROM delivery_discussion AS distb "
            "INNER JOIN user_user AS usertb "
            "ON distb.author_id=usertb.id "
            "WHERE distb.parent_id=0 AND distb.author_id=%s "
            "ORDER BY distb.create_time DESC;",
            (user_id, )
        )
        records_result = cursor.fetchall()
        response_data = list()
        for dis_item in records_result:
            dis_dict = handle_discuss_item(dis_item)
            # 查询回复
            dis_dict['replies'] = get_sub_reply(cursor, dis_item['id'])
            response_data.append(dis_dict)
    return {'message': '查询成功!', 'discussions': response_data, 'total_page': 1}


@discussion_router.get("/delivery/discussion-query/", summary="用户搜索关键字问题")
async def query_keyword_discussion(keyword: str = Query(...)):
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT distb.id,distb.content,distb.create_time,"
            "usertb.username,usertb.phone,usertb.avatar "
            "FROM delivery_discussion AS distb "
            "INNER JOIN user_user AS usertb "
            "ON distb.author_id=usertb.id "
            "WHERE distb.parent_id=0 AND LOCATE(%s,distb.content) > 0 "
            "ORDER BY distb.create_time DESC;",
            (keyword, )
        )
        records_result = cursor.fetchall()
        response_data = list()
        for dis_item in records_result:
            dis_dict = handle_discuss_item(dis_item)
            # 查询回复
            dis_dict['replies'] = get_sub_reply(cursor, dis_item['id'])
            response_data.append(dis_dict)
    return {'message': '查询成功!', 'discussions': response_data, 'total_page': 1}


@discussion_router.get("/delivery/discussion-latest/", summary="获取最新的10条讨论")
async def query_latest_discussion():
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT distb.id,distb.content,distb.create_time,"
            "usertb.username,usertb.phone,usertb.avatar "
            "FROM delivery_discussion AS distb "
            "INNER JOIN user_user AS usertb "
            "ON distb.author_id=usertb.id "
            "WHERE distb.parent_id=0 "
            "ORDER BY distb.create_time DESC "
            "LIMIT 10;",
        )
        records_result = cursor.fetchall()
        response_data = list()
        for dis_item in records_result:
            dis_dict = handle_discuss_item(dis_item)
            # 查询回复
            dis_dict['replies'] = get_sub_reply(cursor, dis_item['id'])
            response_data.append(dis_dict)
        return {'message': '查询成功!', 'discussions': response_data}
