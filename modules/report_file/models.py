# _*_ coding:utf-8 _*_
# @File  : models.py
# @Time  : 2020-09-30 09:14
# @Author: zizle
from enum import Enum
from pydantic import BaseModel


class ReportType(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"
    annual = "annual"


class ReportFileItem(BaseModel):
    """ 报告文件的文件信息 """
    date: str
    relative_varieties: str
    report_type: int
    rename_text: str


class ModifyReportInfo(BaseModel):
    file_date: str
    variety_en: str
    title: str
    file_type: int
    is_active: int
