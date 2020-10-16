# _*_ coding:utf-8 _*_
# @File  : models.py
# @Time  : 2020-09-22 15:50
# @Author: zizle
from pydantic import BaseModel


class WarehouseItem(BaseModel):
    """ 交割仓库验证模型 """
    area: str
    name: str
    short_name: str
    addr: str
    arrived: str = ''
    longitude: float
    latitude: float


class DeliveryVarietyItem(BaseModel):
    """ 仓库可交割品种模型 """
    warehouse_code: str
    variety: str
    variety_en: str
    is_delivery: int
    linkman: str = ''
    links: str = ''
    premium: str = ''
    receipt_unit: str = ''


class VarietyDeliveryMsgItem(BaseModel):
    """ 品种交割信息 """
    variety: str
    variety_en: str
    last_trade: str
    receipt_expire: str
    delivery_unit: str
    limit_holding: str


class DiscussionItem(BaseModel):
    content: str
    parent_id: int = 0


class ReceiptItem(BaseModel):
    """ 交割仓单的模型 """
    warehouse_code: str
    warehouse_name: str
    variety: str
    variety_en: str
    date: str
    receipt: int
    increase: int
