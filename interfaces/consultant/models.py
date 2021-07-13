# _*_ coding:utf-8 _*_
# @File  : models.py
# @Time  : 2021-01-19 10:44
# @Author: zizle
from pydantic import BaseModel


class ConsultArticleItem(BaseModel):
    article_type: str
    content: str
    user_token: str


class StrategyAddItem(BaseModel):
    user_token: str
    content: str


class StrategyModifyItem(BaseModel):
    user_token: str
    content: str
    strategy_id: int