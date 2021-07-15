# _*_ coding:utf-8 _*_
# @File  : menu_op.py
# @Time  : 2021-06-22  16:13
# @Author: zizle
from fastapi import APIRouter, Depends, Body
from pydantic import BaseModel
from status import r_status
from interfaces.depends import admin_logged_require

op_menu_api = APIRouter()


class SystemMenuItem(BaseModel):
    parent_id: int
    name_en: str
    name_zh: str
    icon: str
    category: int


@op_menu_api.post('/menu/', summary='添加菜单')
async def create_system_menus(person: dict = Depends(admin_logged_require),
                              menu_item: SystemMenuItem = Body(...)):
    user_id = person['uid']
    db = RuiZyDBConnection()
    # 查询数量
    count_obj = db.query('SELECT count(id) AS total_count FROM sys_menu;', keep_conn=True)
    sort_index = count_obj[0]['total_count']
    sql = 'INSERT INTO sys_menu (creator,parent_id,category,name_en,name_zh,icon,sorted) ' \
          'VALUES (%s,%s,%s,%s,%s,%s,%s);'
    params = [user_id, menu_item.parent_id, menu_item.category, menu_item.name_en, menu_item.name_zh, menu_item.icon,
              sort_index]
    count, _ = db.insert(sql, params)
    if count:
        return {'code': r_status.CREATED_SUCCESS, 'message': '创建菜单成功!'}
    return {'code': r_status.SERVER_ERROR, 'message': '创建菜单失败了!'}
