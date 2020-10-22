# _*_ coding:utf-8 _*_
# @File  : models.py
# @Time  : 2020-09-03 16:11
# @Author: zizle
from pydantic import BaseModel


class SheetData(BaseModel):
    variety_en: str
    group_id: int
    sheet_name: str
    sheet_headers: list
    sheet_values: list


class ChartOption(BaseModel):
    """ 创建图形配置 """
    title: str
    variety_en: str
    decipherment: str
    is_private: int
    option: dict


class SwapSuffixItem(BaseModel):
    swap_id: int
    to_swap: int
    swap_row: int  # 记录行,返回


class SpotPriceItem(BaseModel):
    """ 现货报价数据模型 """
    date: str
    variety_en: str
    spot_price: float
    price_increase: float


class ModifySpotItem(SpotPriceItem):
    id: int


class UpdateFolderItem(BaseModel):
    """ 配置更新文件夹 """
    client: str
    folder_path: str
    variety_en: str
    group_id: int




