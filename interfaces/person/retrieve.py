# _*_ coding:utf-8 _*_
# @File  : retrieve.py
# @Time  : 2021-06-07 09:59
# @Author: zizle

import datetime
from fastapi import APIRouter, Body, Depends, Query, Path, HTTPException
from pydantic import BaseModel
from status import r_status
from db import FAConnection, RedisConnection
from configs import TOKEN_EXPIRES, ADMIN_FLAG
from hutool import security
from interfaces.depends import admin_logged_require, logged_require
from category import USER_GROUPS

retrieve_api = APIRouter()


class LoginItem(BaseModel):
    account: str
    password: str
    image_code: str = ''
    image_code_uuid: str = ''
    client_uuid: str = ''


@retrieve_api.post('/login.{login_type}/', summary='用户登录')
async def client_user_login(login_type: str = Path(...), login_item: LoginItem = Body(...),
                            auto: int = Query(0, ge=0, le=1)):  # auto是否自动登录
    # 验证图片验证码
    if auto < 1:  # 非自动登录验证图片验证码
        redis_conn = RedisConnection()
        real_img_code = redis_conn.get_value(key=f'{login_item.image_code_uuid}')
        if not real_img_code:
            return {'code': r_status.VALIDATE_ERROR, 'message': '验证码已失效!', 'token': '', 'access': []}
        if real_img_code != login_item.image_code:
            return {'code': r_status.VALIDATE_ERROR, 'message': '验证码错误!', 'token': '', 'access': []}

    account = security.rsa_decrypt(login_item.account, 0)  # 解密手机
    password = security.rsa_decrypt(login_item.password, 0)  # 解密密码

    if not all([account, password]):
        return {'code': r_status.VALIDATE_ERROR, 'message': '用户名和密码不能为空!', 'token': '', 'access': []}

    sql = 'SELECT id,phone,username,nickname,account,password,grouping,is_active FROM sys_person WHERE account=%s;'
    db = FAConnection(conn_name='User Login')
    user_list = db.query(sql, [account])
    token_access = []
    if login_type == 'backadmin':  # 后台管理登录(角色是superuser和operator的)
        user_list = list(filter(lambda x: x['grouping'] <= 2, user_list))
        token_access = [ADMIN_FLAG]
    elif login_type == 'web':  # 网页登录
        pass
    elif login_type == 'client':  # 客户端登录
        pass
    else:
        return {'code': r_status.VALIDATE_ERROR, 'message': '登录方式不支持!', 'token': '', 'access': []}
    if len(user_list) < 1:
        return {'code': r_status.NOT_CONTENT, 'message': '用户不存在或无权限以此方式登录!', 'token': '', 'access': []}
    user_obj = user_list[0]
    # 验证有效性
    if user_obj['is_active'] < 1:
        return {'code': r_status.VALIDATE_ERROR, 'message': '无效用户,不能登录!', 'token': '', 'access': []}
    if user_obj['grouping'] <= 2:
        token_access = [ADMIN_FLAG]
    # 验证密码
    is_password_correct = security.decipher_user_password(password, user_obj['password'])
    if is_password_correct:
        token_data = {
            'uid': user_obj['id'],
            'access': token_access
        }
        # 发放token
        token = security.create_access_token(token_data, expire_seconds=TOKEN_EXPIRES)
        return {'code': r_status.SUCCESS, 'message': '登录成功!', 'token': token, 'access': token_access}
    else:
        return {'code': r_status.VALIDATE_ERROR, 'message': '用户名或密码错误!', 'token': '', 'access': []}

    # account = security.rsa_decrypt(login_item.account, 0)  # 解密手机
    # password = security.rsa_decrypt(login_item.password, 0)  # 解密密码
    # if not all([account, password]):
    #     return {'code': r_status.VALIDATE_ERROR, 'message': '用户名和密码不能为空!', 'token': ''}
    # if auto < 1:  # 非自动登录验证图片验证码
    #     redis_conn = RedisConnection()
    #     real_img_code = redis_conn.get_value(key=f'{login_item.image_code_uuid}')
    #     if not real_img_code:
    #         return {'code': r_status.VALIDATE_ERROR, 'message': '验证码已失效!', 'token': ''}
    #     if real_img_code != login_item.image_code:
    #         return {'code': r_status.VALIDATE_ERROR, 'message': '验证码错误!', 'token': ''}
    # # 查询用户
    # sql = 'SELECT id,phone,username,nickname,account,password,grouping,is_active FROM sys_person WHERE account=%s;'
    # db = FAConnection(conn_name='user-login')
    # user_list = db.query(sql, [account], fetchone=True, keep_conn=True)
    # if len(user_list) < 1:
    #     db.close()
    #     return {'code': r_status.NOT_CONTENT, 'message': '用户不存在!', 'token': ''}
    #
    # user_obj = user_list[0]
    # # 验证用户是否有效
    # if not user_obj['is_active']:
    #     return {'code': r_status.NOT_CONTENT, 'message': '无效用户!', 'token': ''}
    # if not ism:  # 如果不是后台管理登录, 查询用户可登录的客户端
    #     can_login_sql = 'SELECT ctb.client_code,spc.expire FROM sys_person_client AS spc ' \
    #                     'INNER JOIN sys_client AS ctb ' \
    #                     'ON spc.client_id=ctb.id AND spc.user_id=%s AND ctb.client_code=%s;'
    #     login_client_list = db.query(can_login_sql, [user_obj['id'], login_item.client_uuid], fetchone=True)
    #     if len(login_client_list) < 1:
    #         return {'code': r_status.VALIDATE_ERROR, 'message': '账号限制在本客户端登录,请联系管理员开通!', 'token': ''}
    #     login_client = login_client_list[0]
    #     now_date = datetime.datetime.now().strftime('%Y-%m-%d')
    #     if not login_client['expire'] or login_client['expire'].strftime('%Y-%m-%d') < now_date:
    #         return {'code': r_status.VALIDATE_ERROR, 'message': '账号限制在本客户端登录,请联系管理员开通!', 'token': ''}
    # else:  # 后台登录,验证用户是否为后台管理员
    #     db.close()
    #     if user_obj['grouping'] > 2:
    #         return {'code': r_status.VALIDATE_ERROR, 'message': '您没有权限登录后台管理!', 'token': ''}
    #
    # # 验证密码
    # is_password_correct = security.decipher_user_password(password, user_obj['password'])
    # if is_password_correct:  # 密码准确
    #     access = [ADMIN_FLAG] if ism == 1 and user_obj['grouping'] <= 2 else []  # 后台管理员独有的ADMIN_FLAG
    #     data = {
    #         'uid': user_obj['id'],
    #         'account': user_obj['account'],
    #         'username': user_obj['username'],
    #         'nickname': user_obj['nickname'],
    #         'grouping': user_obj['grouping'],
    #         'access': access,
    #     }
    #     # 生成 json web token
    #     token = security.create_access_token(data=data, expire_seconds=TOKEN_EXPIRES)
    #     return {'code': r_status.SUCCESS, 'message': '登录成功!', 'token': token}
    # else:
    #     return {'code': r_status.UN_AUTHORIZATION, 'message': '用户名或密码错误!', 'token': ''}


@retrieve_api.get('/user.info/', summary='使用token获取用户信息')
async def get_user_information(person: dict = Depends(logged_require)):
    user_id = person['uid']
    db = FAConnection()
    sql = 'SELECT id,username,nickname,account,phone,grouping,is_active FROM sys_person WHERE id=%s;'
    user_list = db.query(sql, [user_id])
    if len(user_list) < 1:
        raise HTTPException(status_code=401, detail='login expired')
    user_obj = user_list[0]
    user_obj['nickname'] = user_obj['username'] if not user_obj['nickname'] else user_obj['nickname']
    return {'code': r_status.SUCCESS, 'message': '获取用户信息成功!', 'data': user_obj}


@retrieve_api.get('/user.variety/', summary='查询用户的权限品种')
async def get_user_variety(person: dict = Depends(logged_require)):
    is_all = False
    if ADMIN_FLAG in person['access']:
        sql = 'SELECT id,variety_code,variety_name FROM sys_variety WHERE is_active=1;'
        param = None
        is_all = True
    else:
        sql = 'SELECT v.id,v.variety_code,v.variety_name,expire ' \
              'FROM sys_variety AS v ' \
              'INNER JOIN sys_person_variety AS p ON v.id=p.variety_id ' \
              'WHERE v.is_active=1 AND p.user_id=%s;'
        param = [person['uid']]
    db = FAConnection(conn_name='QueryPersonVariety')
    records = db.query(sql, param)
    rep_data = []
    if not is_all:
        # 过滤掉已过期的
        today_str = datetime.datetime.today().strftime('%Y-%m-%d')
        for item in records:
            if item.get('expire') and item['expire'].strftime('%Y-%m-%d')<today_str:
                continue
            rep_data.append(item)
    else:
        rep_data = records
    return {'code': r_status.SUCCESS, 'message': '查询用户权限品种成功!', 'data': rep_data}


@retrieve_api.get('/users/', summary='查询指定类型的用户列表')
async def get_category_user(person: dict = Depends(admin_logged_require), group: int = Query(..., ge=1, le=5)):
    query_sql = 'SELECT id,username,account,grouping FROM sys_person WHERE grouping<=%s AND is_active=1;'
    db = FAConnection()
    users = db.query(query_sql, [group])
    for u in users:
        u['group_name'] = USER_GROUPS.get(u['grouping'], '未知')
    return {'code': r_status.SUCCESS, 'message': '查询{}用户成功!', 'users': users}
