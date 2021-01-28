# _*_ coding:utf-8 _*_
# @File  : article.py
# @Time  : 2021-01-19 10:36
# @Author: zizle

import datetime
from fastapi import APIRouter, HTTPException, Body
from db.mysql_z import MySqlZ
from utils.verify import decipher_user_token

from .models import ConsultArticleItem

article_api = APIRouter()


# 根据类型获取文章内容
@article_api.get('/{article_type}/')
async def get_content(article_type:str):
    if article_type not in ['person', 'organization', 'riskmanager', 'otcoption', 'safefutures']:
        raise HTTPException(status_code=400, detail='参数错误,article_type Error!')
    # 查询数据
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id,content FROM product_consultant WHERE article_type=%s;",
            (article_type, )
        )
        article = cursor.fetchone()
    article = {} if not article else article
    return {'message': '查询成功!', 'article': article}


# 根据类型创建一篇文章
@article_api.post('/{article_type}/')
async def create_content(article_type: str, content_item: ConsultArticleItem = Body(...), ):
    if article_type not in ['person', 'organization', 'riskmanager', 'otcoption', 'safefutures']:
        raise HTTPException(status_code=400, detail='参数错误,article_type Error!')
    user_id, _ = decipher_user_token(content_item.user_token)
    if not user_id:
        raise HTTPException(status_code=400, detail='user_token Error!')
    # 创建内容
    now_timestamp = int(datetime.datetime.now().timestamp())
    with MySqlZ() as cursor:
        count = cursor.execute(
            "UPDATE product_consultant SET update_time=%s,content=%s,author_id=%s "
            "WHERE article_type=%s;",
            (now_timestamp, content_item.content, user_id, article_type)
        )
        if count<1:
            # 创建
            cursor.execute(
                "INSERT INTO product_consultant (create_time,update_time,article_type,content,author_id) "
                "VALUES (%s,%s,%s,%s,%s);",
                (now_timestamp, now_timestamp, article_type, content_item.content, user_id)
            )

    return {'message': '创建成功!'}

