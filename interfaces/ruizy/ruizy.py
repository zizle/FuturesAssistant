# _*_ coding:utf-8 _*_
# @File  : ruizy.py
# @Time  : 2021-07-13 15:16
# @Author: zizle

from fastapi import APIRouter, Query, Path, Depends, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from hutool.security import generate_image_code
from hutool.utils import list2tree
from db import RedisConnection, FAConnection
from interfaces.depends import admin_logged_require, logged_require
from category import MENUS
from status import r_status
from configs import ADMIN_FLAG

ruizy_api = APIRouter()


@ruizy_api.get('/image-code/', summary='获取图片验证码')
async def get_image_code(img_uuid: str = Query(...)):
    image_buf, text = generate_image_code()
    # 将验证码存入redis
    redis_conn = RedisConnection()
    redis_conn.set_value(key=f'{img_uuid}', value=text, expires=120)
    return StreamingResponse(content=image_buf)


@ruizy_api.get('/menu.{menu_type}/', summary='获取菜单')
async def get_system_menu(menu_type: str = Path(...)):
    if menu_type == 'all':
        category = 0
    elif menu_type == 'backadmin':
        category = 1
    elif menu_type == 'web':
        category = 2
    elif menu_type == 'client':
        category = 3
    else:
        return {'code': r_status.VALIDATE_ERROR, 'message': 'menu type Error!', 'data': []}
    sql = 'SELECT id,parent_id,category,icon,name_en,name_zh FROM sys_menu WHERE IF(0=%s,TRUE,category=%s) AND is_active=1 ' \
          'ORDER BY sorted;'
    db = FAConnection(conn_name='query menus')
    records = db.query(sql, [category, category])
    for item in records:
        item['category_text'] = MENUS.get(item['category'], '未知')
    menus = list2tree(records, 0)
    return {'code': r_status.SUCCESS, 'message': '获取菜单成功!', 'data': menus}


class SystemMenuItem(BaseModel):
    parent_id: int
    name_en: str
    name_zh: str
    icon: str
    category: int


@ruizy_api.post('/menu/', summary='增加一个菜单')
async def create_menu(person: dict = Depends(admin_logged_require), menu_item: SystemMenuItem = Body(...)):
    user_id = person['uid']
    db = FAConnection()
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

