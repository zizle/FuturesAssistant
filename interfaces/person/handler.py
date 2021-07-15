# _*_ coding:utf-8 _*_
# @File  : handler.py
# @Time  : 2021-06-08 13:32
# @Author: zizle

# 各种接口处理使用的函数

from hutool import security
from status import r_status
from db_util import RuiZyDBConnection
from settings import ADMIN_FLAG, TOKEN_EXPIRES


def user_login_handler(query_sql: str, account, password):
    account = security.rsa_decrypt(account, 0)  # 解密手机
    password = security.rsa_decrypt(password, 0)  # 解密密码
    if not all([account, password]):
        return {'code': r_status.VALIDATE_ERROR, 'message': '用户名和密码不能为空!', 'token': ''}
    # 查询用户
    db = RuiZyDBConnection()
    user_obj_list = db.query(query_sql, [account], fetchone=True)
    if len(user_obj_list) < 1:
        return {'code': r_status.NOT_CONTENT, 'message': '用户不存在!', 'token': ''}
    user_obj = user_obj_list[0]
    # 验证password
    is_password_correct = security.decipher_user_password(password, user_obj['password'])
    if is_password_correct:  # 密码准确
        data = {
            'uid': user_obj['id'],
            'account': user_obj['account'],
            'access': [ADMIN_FLAG],
        }
        # 生成 json web token
        token = security.create_access_token(data=data, expire_seconds=TOKEN_EXPIRES)
        return {'code': r_status.SUCCESS, 'message': '登录成功!', 'token': token}
    else:
        return {'code': r_status.UN_AUTHORIZATION, 'message': '用户名或密码错误!', 'token': ''}
