# _*_ coding:utf-8 _*_
# @File  : models.py
# @Time  : 2020-08-31 8:29
# @Author: zizle
from typing import Optional
from enum import Enum
from pydantic import BaseModel


class UserRole(Enum):
    all: str = "all"
    superuser: str = "superuser"
    operator: str = "operator"
    collector: str = "collector"
    research: str = "research"
    normal: str = "normal"


class JwtToken(BaseModel):
    show_username: str
    access_token: str
    token_type: str


class User(BaseModel):
    id: int = None
    user_code: str
    username: str
    phone: str
    email: str
    role: str
    is_active: Optional[bool] = True


class UserInDB(User):
    password_hashed: str


class ModifyUserItem(BaseModel):
    """ 修改用户基本信息 """
    modify_id: int = None
    username: str
    user_code: str
    phone: str
    email: str
    role: str
    is_active: int
    note: str


class ModuleItem(BaseModel):
    module_id: str
    module_text: str
    client_uuid: str
    user_token: str = None


class UserModuleAuthItem(BaseModel):
    """ 修改用户模块权限 """
    modify_user: int
    expire_date: str
    module_id: str
    module_text: str


class UserClientAuthItem(BaseModel):
    """ 修改客户端登录权限 """
    modify_user: int
    expire_date: str
    client_id: int


class UserVarietyAuthItem(BaseModel):
    """ 修改客户端登录权限 """
    modify_user: int
    expire_date: str
    variety_id: int
    variety_en: str


class UserExtensionItem(BaseModel):
    """ 用户的拓展信息 """
    user_id: int
    wx_id: str