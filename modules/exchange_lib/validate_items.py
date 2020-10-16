# _*_ coding:utf-8 _*_
# @File  : validate_items.py
# @Time  : 2020-07-24 8:02
# @Author: zizle
from pydantic import BaseModel


class DailyItem(BaseModel):
    date: str
    variety_en: str
    contract: str
    open_price: float
    highest: float
    lowest: float
    close_price: float
    settlement: float
    zd_1: float
    zd_2: float
    trade_volume: int
    empty_volume: int


class RankItem(BaseModel):
    date: str
    variety_en: str
    contract: str
    rank: int
    trade_company: str
    trade: int
    trade_increase: int
    long_position_company: str
    long_position: int
    long_position_increase: int
    short_position_company: str
    short_position: int
    short_position_increase: int

class ReceiptItem(BaseModel):
    date: str
    variety_en: str
    warehouse: str
    receipt: int
    receipt_increase: int


class CZCEDailyItem(DailyItem):
    pre_settlement: float
    increase_volume: int
    trade_price: float
    delivery_price: float


class CZCERankItem(RankItem):
    pass


class CZCEReceiptItem(ReceiptItem):
    premium_discount: float


class SHFEReceiptItem(ReceiptItem):
    pass

class DCEReceiptItem(ReceiptItem):
    pass


class SHFEDailyItem(DailyItem):
    pre_settlement: float
    increase_volume: int


class SHFERankItem(RankItem):
    pass


class CFFEXDailyItem(DailyItem):
    trade_price: float


class CFFEXRankItem(RankItem):
    pass


class DCEDailyItem(DailyItem):
    pre_settlement: float
    increase_volume: int
    trade_price: float


class DCERankItem(RankItem):
    pass
