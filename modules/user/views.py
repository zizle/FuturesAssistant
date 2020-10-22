# _*_ coding:utf-8 _*_
# @File  : views.py
# @Time  : 2020-08-31 11:38
# @Author: zizle

""" 用户的其他操作 """
from datetime import datetime
from fastapi import APIRouter, Query, Depends, Body, HTTPException
from fastapi.encoders import jsonable_encoder
from utils.verify import oauth2_scheme, decipher_user_token
from db.mysql_z import MySqlZ
from .models import UserRole, ModifyUserItem, UserExtensionItem


user_view_router = APIRouter()


@user_view_router.get("/user/phone-exists/", summary="查询手机号是否存在")
async def get_phone(phone: str = Query(..., min_length = 11, max_length = 11, regex = r'^[1][3-9][0-9]{9}$')):
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT `id`,`phone` FROM user_user WHERE phone=%s;", phone
        )
        is_exists = cursor.fetchone()
    if is_exists:
        return {"message": "查询成功!", "is_exists": True}
    else:
        return {"message": "查询成功!", "is_exists": False}


@user_view_router.put("/user/online/", summary="用户在线时间累计")
async def update_user_online(
        machine_uuid: str = Query(..., min_length = 36, max_length = 36),
        token: str = Depends(oauth2_scheme)
):
    user_id, user_code = decipher_user_token(token)
    today_str = datetime.today().strftime("%Y-%m-%d")
    with MySqlZ() as cursor:
        cursor.execute("SELECT `id`,machine_uuid FROM `basic_client` WHERE machine_uuid=%s;", machine_uuid)
        client_info = cursor.fetchone()
        if client_info:  # 客户端存在查询今日是否有记录,有则追加更新,无则新建一条2分钟的记录
            cursor.execute(
                "SELECT `id` online_date FROM basic_client_online WHERE online_date=%s AND client_id=%s;",
                (today_str, client_info["id"])
            )
            if cursor.fetchone():
                cursor.execute(
                    "UPDATE `basic_client_online` "
                    "SET total_online=total_online+2 "
                    "WHERE online_date=%s AND client_id=%s;",
                    (today_str, client_info["id"])
                )
            else:
                cursor.execute(
                    "INSERT INTO basic_client_online (client_id,online_date,total_online) "
                    "VALUES (%s,%s,%s);", (client_info["id"], today_str, 2)
                )
        if user_id:
            cursor.execute(
                "SELECT id,online_date FROM user_user_online WHERE online_date=%s AND user_id=%s;",
                (today_str, user_id)
            )
            if cursor.fetchone():
                cursor.execute(
                    "UPDATE `user_user_online` SET total_online=total_online+2 "
                    "WHERE online_date=%s AND user_id=%s;",
                    (today_str, user_id)
                )
            else:
                cursor.execute(
                    "INSERT INTO user_user_online (user_id,online_date,total_online) "
                    "VALUES (%s,%s,%s);", (user_id, today_str, 2)
                )
    return {"message": "用户更新在线时间成功!"}


@user_view_router.get("/all-users/", summary="获取指定的用户")
async def all_users(role: UserRole = Query(...), user_token: str = Depends(oauth2_scheme)):
    user_id, _ = decipher_user_token(user_token)   # 用户登录了才能获取
    if not user_id:
        return {"message": "查询用户成功!", "users": [], "query_role": ""}
    with MySqlZ() as cursor:
        cursor.execute("SELECT `id`,role FROM user_user WHERE `id`=%s;", (user_id, ))
        user_info = cursor.fetchone()
        if not user_info:
            return {"message": "查询用户成功!", "users": [], "query_role": ""}
        if user_info["role"] not in [role.superuser.name, role.operator.name]:
            return {"message": "查询用户成功!", "users": [], "query_role": user_info["role"]}
        cursor.execute(
            "SELECT `id`,username,DATE_FORMAT(join_time,'%%Y-%%m-%%d') AS `join_time`, DATE_FORMAT(recent_login,'%%Y-%%m-%%d') AS `recent_login`,"
            "user_code,phone,email,role,is_active,note "
            "FROM user_user "
            "WHERE IF('all'=%s,TRUE,role=%s);",
            (role.name, role.name)
        )
        all_user = cursor.fetchall()
    return {"message": "查询用户成功!", "users": all_user, "query_role": user_info["role"]}


@user_view_router.put("/user/info/", summary="用户的基本信息修改")
async def modify_user_information(
        operator_token: str = Depends(oauth2_scheme),
        user_info: ModifyUserItem = Body(...)
):
    operate_user, _ = decipher_user_token(operator_token)
    if not operate_user:
        raise HTTPException(status_code=401, detail="登录信息过期了,重新登录再操作!")
    if user_info.modify_id:  # 管理者修改用户信息
        # 查询管理者身份
        with MySqlZ() as cursor:
            cursor.execute("SELECT id,role FROM user_user WHERE id=%s;", (operate_user, ))
            operator = cursor.fetchone()
            if not operator or operator["role"] not in ["superuser", "operator"]:
                raise HTTPException(status_code=401, detail="非法用户或无权限,无法操作!")
            if operator["role"] != "superuser" and user_info.role == "operator":
                raise HTTPException(status_code=401, detail="您不能设置用户角色为运营者!")
            # 进行用户信息的修改
            cursor.execute(
                "UPDATE user_user SET username=%(username)s,phone=%(phone)s,email=%(email)s,"
                "role=%(role)s,is_active=%(is_active)s,note=%(note)s "
                "WHERE id=%(modify_id)s;",
                jsonable_encoder(user_info)
            )
        return {"message": "修改 {} 的信息成功!".format(user_info.user_code)}

    else:  # 用户自己修改信息
        return {"message": "修改成功!"}


@user_view_router.get("/user/extension/", summary="用户的拓展信息项")
async def get_searcher_wxid(
        user_type: str = Query('inner'),
        phone: str = Query('')
):
    if user_type not in ["inner", "normal"]:
        return {"message": "用户拓展信息", "users": []}
    if user_type == "inner":
        query_statement = "SELECT usertb.id,usertb.phone,usertb.username,usertb.note," \
                          "userextb.wx_id " \
                          "FROM user_user AS usertb " \
                          "LEFT JOIN user_user_extension AS userextb " \
                          "ON usertb.id=userextb.user_id " \
                          "WHERE usertb.role<>'normal' AND IF(%s='',TRUE,usertb.phone=%s);"
    else:
        query_statement = "SELECT usertb.id,usertb.phone,usertb.username,usertb.note," \
                          "userextb.wx_id " \
                          "FROM user_user AS usertb " \
                          "LEFT JOIN user_user_extension AS userextb " \
                          "ON usertb.id=userextb.user_id " \
                          "WHERE usertb.role='normal' AND IF(%s='',TRUE,usertb.phone=%s);"

    with MySqlZ() as cursor:
        cursor.execute(query_statement, (phone, phone))
        users = cursor.fetchall()

    return {"message": "用户拓展信息", "users": users}


@user_view_router.put("/user/extension/{user_id}/", summary="修改用户拓展信息")
async def modify_user_extension(user_id: int, extension_item: UserExtensionItem = Body(...)):
    with MySqlZ() as cursor:
        cursor.execute("SELECT id,user_id FROM user_user_extension WHERE user_id=%s; ", (user_id, ))
        exist = cursor.fetchone()
        if exist:
            cursor.execute(
                "UPDATE user_user_extension SET wx_id=%(wx_id)s WHERE user_id=%(user_id)s;",
                jsonable_encoder(extension_item)
            )
        else:
            cursor.execute(
                "INSERT INTO user_user_extension (user_id,wx_id) VALUES (%(user_id)s, %(wx_id)s);",
                jsonable_encoder(extension_item)
            )

    return {"message": "修改成功"}
