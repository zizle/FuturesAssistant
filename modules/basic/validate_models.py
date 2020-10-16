# _*_ coding:utf-8 _*_
# @File  : validate_models.py
# @Time  : 2020-08-31 9:01
# @Author: zizle
from enum import Enum
from pydantic import BaseModel


class ClientItem(BaseModel):
    client_name: str
    machine_uuid: str
    is_manager: bool


class ModifyClient(BaseModel):
    client_id: int
    client_name: str
    is_manager: int
    is_active: int
    client_uuid: str


class ExchangeLib(Enum):
    shfe: str = "shfe"              # 上海期货交易所
    czce: str = "czce"              # 郑州商品交易所
    dce: str = "dce"                # 大连商品交易所
    cffex: str = "cffex"            # 中国金融期货交易所
    ine: str = "ine"                # 上海国际能源中心


class ExchangeLibCN(Enum):
    shfe: str = "上海期货交易所"
    czce: str = "郑州商品交易所"
    dce: str = "大连商品交易所"
    cffex: str = "中国金融期货交易所"
    ine: str = "上海国际能源中心"


class VarietyGroup(Enum):
    finance: str = "finance"       # 金融股指
    farm: str = "farm"             # 农副产品
    chemical: str = "chemical"     # 能源化工
    metal: str = "metal"           # 金属产业


class VarietyGroupCN(Enum):
    finance: str = "金融股指"
    farm: str = "农副产品"
    chemical: str = "能源化工"
    metal: str = "金属产业"



class VarietyItem(BaseModel):
    """ 添加品种的验证项 """
    variety_name: str
    variety_en: str
    exchange_lib: ExchangeLib
    group_name: VarietyGroup

