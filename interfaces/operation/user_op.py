# _*_ coding:utf-8 _*_
# @File  : user_op.py
# @Time  : 2021-06-10 15:06
# @Author: zizle
import datetime

import pandas as pd
from fastapi import APIRouter, Depends, Body, Query, Path
from pydantic import BaseModel
from db import FAConnection
from interfaces.depends import admin_logged_require
from hutool import security
from status import r_status
from hutool.utils import create_random_string
from category import USER_GROUPS, VARIETY_GROUPS, EXCHANGE

op_user_api = APIRouter()


# ############################# 用户 ######################################

class UserItem(BaseModel):
    username: str
    account: str
    password: str
    grouping: int
    nickname: str = ''
    phone: str = ''
    reset_pwd: bool


# uop = user-operation用户管理
@op_user_api.post('/user/', summary='添加一个用户')
async def create_user(person: dict = Depends(admin_logged_require), user_item: UserItem = Body(...)):
    # 解密得到account和password
    user_id = person['uid']
    account = security.rsa_decrypt(user_item.account, key_tuple=0)
    password = security.rsa_decrypt(user_item.password, key_tuple=0)
    hash_password = security.cipher_user_password(password)
    if user_item.reset_pwd:  # 初始密码是手机号后6位，无填写手机号则为r123456
        raw_psd = user_item.phone[-6:] if user_item.phone else 'r123456'
        hash_password = security.cipher_user_password(raw_psd)
    if not password and not user_item.reset_pwd:  # 没设置密码也没使用初始密码
        return {'code': r_status.VALIDATE_ERROR, 'message': '请设置密码或勾选系统初始化重置!'}
    # 没有用户名，就随机生成一个
    if not user_item.username:
        username = 'Rui_' + create_random_string(10)
    else:
        username = user_item.username
    sql = 'INSERT INTO sys_person (creator,username,account,password,grouping,nickname,phone) ' \
          'VALUES (%s,%s,%s,%s,%s,%s,%s);'
    db = FAConnection()
    count, _ = db.insert(sql, [user_id, username, account, hash_password, user_item.grouping, user_item.nickname,
                               user_item.phone])
    if count:
        return {'code': r_status.CREATED_SUCCESS, 'message': '创建用户成功!'}
    else:
        return {'code': r_status.SERVER_ERROR, 'message': '创建用户失败,原因未知!'}


@op_user_api.get('/user/', summary='获取用户列表')
async def get_system_users(person: dict = Depends(admin_logged_require), page: int = Query(..., ge=1),
                           page_size: int = Query(..., ge=10, le=200)):
    record_start = (page - 1) * page_size
    record_offset = page_size
    sql = 'SELECT SQL_CALC_FOUND_ROWS id,username,nickname,account,phone,grouping,is_active FROM sys_person ' \
          'ORDER BY create_time DESC LIMIT %s,%s;'
    db = FAConnection()
    records = db.query(sql, param=[record_start, record_offset], keep_conn=True)
    total_obj = db.query('SELECT FOUND_ROWS() AS total;', fetchone=True)
    total_count = total_obj[0]['total'] if total_obj else 0  # 当前总数量
    for user_item in records:
        user_item['group_name'] = USER_GROUPS.get(user_item['grouping'], '未知')
    return {'code': r_status.SUCCESS, 'message': '查询成功!', 'users': records, 'page': page, 'page_size': page_size,
            'total_count': total_count}


@op_user_api.put('/user/{op_id}/', summary='修改一个用户的信息')
async def put_system_user(person: dict = Depends(admin_logged_require), user_item: UserItem = Body(...),
                          op_id: int = Path(..., ge=1)):
    if user_item.reset_pwd:
        password = security.cipher_user_password(user_item.password)
        sql = 'UPDATE sys_person SET username=%s,grouping=%s,password=%s,nickname=%s,phone=%s ' \
              'WHERE id=%s LIMIT 1;'
        params = [user_item.username, user_item.grouping, user_item.nickname, user_item.phone, password, op_id]
    else:
        sql = 'UPDATE sys_person SET username=%s,grouping=%s,nickname=%s,phone=%s ' \
              'WHERE id=%s LIMIT 1;'
        params = [user_item.username, user_item.grouping, user_item.nickname, user_item.phone, op_id]
    db = RuiZyDBConnection()
    success = db.execute(sql, params)
    if success:
        return {'code': r_status.SUCCESS, 'message': '修改成功!'}
    else:
        return {'code': r_status.SUCCESS, 'message': '修改失败,原因未知!'}


@op_user_api.delete('/user/{user_id}/', summary='删除一个用户记录')
async def delete_system_user(person: dict = Depends(admin_logged_require), user_id: int = Path(..., ge=1)):
    # 设置为无效状态
    sql = 'UPDATE sys_person SET is_active=0 WHERE id=%s;'
    db = RuiZyDBConnection()
    success = db.execute(sql, [user_id])
    if success:
        return {'code': r_status.SUCCESS, 'message': '删除成功!'}
    else:
        return {'code': r_status.SUCCESS, 'message': '删除失败,原因未知!'}


# ############################# 用户客户端权限 ######################################


@op_user_api.get('/user/client/', summary='获取客户端信息及用户可登录')
async def get_client_user(u: int = Query(..., ge=1), page: int = Query(..., ge=1),
                          page_size: int = Query(..., ge=10, le=100)):
    record_start = (page - 1) * page_size
    record_offset = page_size
    sql = 'SELECT SQL_CALC_FOUND_ROWS ctb.id,ctb.client_name,ctb.client_code,ctb.category,' \
          'pctb.user_id,pctb.expire ' \
          'FROM sys_client AS ctb ' \
          'LEFT JOIN sys_person_client AS pctb ' \
          'ON ctb.id=pctb.client_id AND pctb.user_id=%s ' \
          'WHERE ctb.is_active=1 LIMIT %s,%s;'
    db = RuiZyDBConnection()
    records = db.query(sql, [u, record_start, record_offset], keep_conn=True)
    total_obj = db.query('SELECT FOUND_ROWS() AS total;')
    total_count = total_obj[0]['total'] if total_obj else 0  # 当前总数量
    for item in records:
        item['category_name'] = CLIENT['CATEGORY'].get(item['category'], '未知')
        if not item['user_id']:
            item['expire'] = ''
            item['can_login'] = 0
        else:  # expire>=now可登录
            expire = item['expire'].strftime('%Y-%m-%d')
            item['expire'] = expire
            if expire >= datetime.datetime.now().strftime('%Y-%m-%d'):
                item['can_login'] = 1
            else:
                item['can_login'] = 0
        del item['user_id']
    return {'code': r_status.SUCCESS, 'message': '查询客户端成功!', 'page': page, 'page_size': page_size,
            'data': records, 'total_count': total_count}


class UserClientAuth(BaseModel):
    user_id: int
    expire: str


@op_user_api.post('/user/client/{client_id}/', summary='新建一个用户可登录记录')
async def create_user_client_login(person: dict = Depends(admin_logged_require), client_id: int = Path(..., ge=1),
                                   auth_item: UserClientAuth = Body(...)):
    sql = 'INSERT IGNORE INTO sys_person_client (creator,user_id,client_id,expire) VALUES (%s,%s,%s,%s);'
    db = RuiZyDBConnection()
    count, _ = db.insert(sql, [person['uid'], auth_item.user_id, client_id, auth_item.expire])
    if count:
        return {'code': r_status.CREATED_SUCCESS, 'message': '创建成功!'}
    else:
        return {'code': r_status.UNKNOWN_ERROR, 'message': '创建失败,原因未知!'}


@op_user_api.put('/user/client/{client_id}/', summary='修改一个用户可登录记录')
async def update_user_client_login(person: dict = Depends(admin_logged_require), client_id: int = Path(..., ge=1),
                                   auth_item: UserClientAuth = Body(...)):
    sql = 'UPDATE sys_person_client SET creator=%s, expire=%s WHERE user_id=%s AND client_id=%s;'
    db = RuiZyDBConnection()
    success = db.execute(sql, [person['uid'], auth_item.expire, auth_item.user_id, client_id])
    if success:
        return {'code': r_status.SUCCESS, 'message': '修改成功!'}
    else:
        return {'code': r_status.UNKNOWN_ERROR, 'message': '修改失败,原因未知!'}


# ############################# 用户功能权限 ######################################

@op_user_api.get('/user/menu/', summary='用户菜单权限查询')
async def get_user_menu_auth(u: int = Query(..., ge=1)):
    sql = 'SELECT smtb.id,smtb.parent_id,smtb.category,smtb.name_en,smtb.name_zh,pm.expire ' \
          ' FROM sys_menu AS smtb ' \
          'LEFT JOIN sys_person_menu AS pm ' \
          'ON smtb.id=pm.menu_id AND pm.user_id=%s ' \
          'ORDER BY smtb.create_time;'
    db = RuiZyDBConnection()
    records = db.query(sql, [u])
    df = pd.DataFrame(records)
    now_date = datetime.datetime.now().strftime('%Y-%m-%d')
    df['expire'] = df['expire'].apply(lambda x: '' if x is None else x.strftime('%Y-%m-%d'))
    df['auth'] = df['expire'].apply(lambda x: 1 if x and x >= now_date else 0)
    df['category_name'] = df['category'].apply(lambda x: MENUS['CATEGORY'].get(x, '未知'))
    # 取parent_id=0
    parent_df = df[df['parent_id'] == 0]
    rep_data = []

    for row in range(parent_df.shape[0]):
        row_df = parent_df[row: row + 1]
        menu_obj = row_df.to_dict(orient='records')[0]
        child_df = df[df['parent_id'] == menu_obj['id']].copy()
        if not menu_obj['auth']:
            child_df['auth'] = [0 for _ in range(child_df.shape[0])]
        menu_obj['children'] = child_df.to_dict(orient='records')

        menu_obj['_showChildren'] = 1  # 前端树形图表格默认展开的标志
        rep_data.append(menu_obj)
    return {'code': r_status.SUCCESS, 'message': '查询菜单权限成功!', 'data': rep_data}


class UserMenuAuth(BaseModel):
    user_id: int
    expire: str


@op_user_api.post('/user/menu/{menu_id}/', summary='新建一个用户功能权限记录')
async def create_user_menu(person: dict = Depends(admin_logged_require), menu_id: int = Path(..., ge=1),
                           auth_item: UserMenuAuth = Body(...)):
    sql = 'INSERT IGNORE INTO sys_person_menu (creator,user_id,menu_id,expire) VALUES (%s,%s,%s,%s);'
    db = RuiZyDBConnection()
    count, _ = db.insert(sql, [person['uid'], auth_item.user_id, menu_id, auth_item.expire])
    if count:
        return {'code': r_status.CREATED_SUCCESS, 'message': '创建成功!'}
    else:
        return {'code': r_status.UNKNOWN_ERROR, 'message': '创建失败,原因未知!'}


@op_user_api.put('/user/menu/{menu_id}/', summary='修改一个用户功能权限记录')
async def put_user_menu(person: dict = Depends(admin_logged_require), menu_id: int = Path(..., ge=1),
                        auth_item: UserMenuAuth = Body(...)):
    sql = 'UPDATE sys_person_menu SET creator=%s, expire=%s WHERE user_id=%s AND menu_id=%s;'
    db = RuiZyDBConnection()
    success = db.execute(sql, [person['uid'], auth_item.expire, auth_item.user_id, menu_id])
    if success:
        return {'code': r_status.SUCCESS, 'message': '修改成功!'}
    else:
        return {'code': r_status.UNKNOWN_ERROR, 'message': '修改失败,原因未知!'}

# ############################# 用户品种权限 ######################################


@op_user_api.get('/user/variety/', summary='用户品种权限查询')
async def get_variety_user(u: int = Query(..., ge=1)):
    sql = 'SELECT vtb.id,vtb.category,vtb.exchange,vtb.variety_name,vtb.variety_code,spv.expire ' \
          'FROM sys_variety AS vtb ' \
          'LEFT JOIN sys_person_variety AS spv ' \
          'ON vtb.id=spv.variety_id AND spv.user_id=%s;'
    db = FAConnection(conn_name='query user.variety')
    records = db.query(sql, [u])
    now_str = datetime.datetime.now().strftime('%Y-%m-%d')
    for item in records:
        item['category_name'] = VARIETY_GROUPS.get(item['category'], '未知')
        item['exchange_name'] = EXCHANGE.get(item['exchange'], '未知')
        item['expire'] = item['expire'].strftime('%Y-%m-%d') if item['expire'] else ''
        item['is_auth'] = 0
        if item['expire'] and item['expire'] >= now_str:
            item['is_auth'] = 1
        if u == 1:
            item['is_auth'] = 1
            item['expire'] = '9999-99-99'
    return {'code': r_status.SUCCESS, 'message': '查询用户品种权限成功!', 'data': records}


class UserVarietyAuth(BaseModel):
    user_id: int
    expire: str


@op_user_api.post('/user/variety/{variety_id}/', summary='添加用户品种权限')
async def create_user_menu(person: dict = Depends(admin_logged_require), variety_id: int = Path(..., ge=1),
                           auth_item: UserMenuAuth = Body(...)):
    sql = 'INSERT IGNORE INTO sys_person_variety (creator,user_id,variety_id,expire) VALUES (%s,%s,%s,%s);'
    db = FAConnection()
    count, _ = db.insert(sql, [person['uid'], auth_item.user_id, variety_id, auth_item.expire])
    if count:
        return {'code': r_status.CREATED_SUCCESS, 'message': '创建成功!'}
    else:
        return {'code': r_status.UNKNOWN_ERROR, 'message': '创建失败,原因未知!'}


@op_user_api.put('/user/variety/{variety_id}/', summary='修改一个用户品种权限记录')
async def put_user_menu(person: dict = Depends(admin_logged_require), variety_id: int = Path(..., ge=1),
                        auth_item: UserVarietyAuth = Body(...)):
    sql = 'UPDATE sys_person_variety SET creator=%s, expire=%s WHERE user_id=%s AND variety_id=%s;'
    db = RuiZyDBConnection()
    success = db.execute(sql, [person['uid'], auth_item.expire, auth_item.user_id, variety_id])
    if success:
        return {'code': r_status.SUCCESS, 'message': '修改成功!'}
    else:
        return {'code': r_status.UNKNOWN_ERROR, 'message': '修改失败,原因未知!'}
