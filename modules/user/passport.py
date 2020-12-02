# _*_ coding:utf-8 _*_
# @File  : passport.py
# @Time  : 2020-08-31 8:24
# @Author: zizle
""" 用户登录、注册 """
import re
import time
import base64
import random
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from fastapi import APIRouter, Form, File, UploadFile, Depends, Body, Query, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import HTTPException
from fastapi.responses import StreamingResponse
from pymysql.err import IntegrityError
from utils import verify
from utils.client import encryption_uuid
from db.redis_z import RedisZ
from db.mysql_z import MySqlZ
from configs import logger, SYSTEM_EMAIL, SYSTEM_EMAIL_AUTH
from modules.basic.validate_models import ExchangeLibCN, VarietyGroupCN
from .models import (JwtToken, User, UserInDB, ModuleItem, UserModuleAuthItem, UserClientAuthItem, UserVarietyAuthItem,
                     ModifyPasswordItem, ResetPasswordEmail)


passport_router = APIRouter()


async def checked_image_code(input_code: str = Form(...), code_uuid: str = Form(...)):
    """ 验证图形验证码的依赖项 """
    with RedisZ() as r:
        real_image_code = r.get(code_uuid)  # 使用code_uuid取得redis中的验证码
    if not real_image_code or input_code.lower() != real_image_code.lower():
        return False
    return True


async def get_default_role():
    """ 根据客户端类型获取默认的用户角色 """
    # with MySqlZ() as cursor:
    #     cursor.execute("SELECT `id`,`is_manager` FROM basic_client WHERE machine_uuid=%s;", client_token)
    #     client = cursor.fetchone()
    # if client["is_manager"]:
    #     return "research"
    # else:
    #     return "normal"
    # 2020.11.23修改： 由于客户端唯一识别号重复的问题，这个改为默认"normal"
    return "normal"


@passport_router.post("/register/", summary="用户注册")
async def register(
        is_image_code_passed: bool = Depends(checked_image_code),
        role: str = Depends(get_default_role),
        phone: str = Form(...),
        username: str = Form(""),
        email: str = Form(""),
        password: str = Form(...),
        client_uuid: str = Form(...),
        is_manager: int = Form(0)
):
    if not is_image_code_passed:
        return {"message": "验证码有误!", "user": {}}
    # 解码phone和password
    phone = base64.b64decode(phone.encode('utf-8')).decode('utf-8')
    password = base64.b64decode(password.encode('utf-8')).decode('utf-8')
    # 手动验证邮箱和手机号
    if not re.match(r'^([a-zA-Z0-9]+[_|\_|\.]?)*[a-zA-Z0-9]+@([a-zA-Z0-9]+[_|\_|\.]?)*[a-zA-Z0-9]+\.[a-zA-Z]{2,3}$', email):
        return {"message": "邮箱格式有误!", "user": {}}
    if not re.match(r'^[1][3-9][0-9]{9}$', phone):
        return {"message": "手机号格式有误!", "user": {}}
    # 将用户信息保存到数据库中
    user_to_save = UserInDB(
        user_code=verify.generate_user_unique_code(),
        username=username,
        phone=phone,
        email=email,
        role="research" if is_manager else "normal",
        password_hashed=verify.get_password_hash(password)  # hash用户密码
    )
    try:
        with MySqlZ() as cursor:
            cursor.execute(
                "INSERT INTO `user_user` (`user_code`,`username`,`phone`,`email`,`password_hashed`,`role`) "
                "VALUES (%(user_code)s,%(username)s,%(phone)s,%(email)s,%(password_hashed)s,%(role)s);",
                (jsonable_encoder(user_to_save))
            )
            # 创建用户可登录的客户端
            new_user_id = cursor._instance.insert_id()
            machine_uuid = encryption_uuid(client_uuid, new_user_id)
            # 新增客户端
            cursor.execute(
                "INSERT IGNORE INTO basic_client (client_name,machine_uuid,is_manager) "
                "VALUES (%s,%s,%s);",
                (username, machine_uuid, is_manager)
            )
            # 添加客户端用户可登录的客户端表
            new_client_id = cursor._instance.insert_id()
            cursor.execute(
                "INSERT INTO `user_user_client` (user_id,client_id,expire_date) "
                "VALUES (%s,%s,%s);",
                (new_user_id, new_client_id, "3000-01-01")
            )
    except IntegrityError as e:
        logger.error("用户注册失败:{}".format(e))
        return {"message": "手机号已存在!", "user": {}}
    back_user = User(
        user_code=user_to_save.user_code,
        username=user_to_save.username,
        phone=user_to_save.phone,
        email=user_to_save.email,
        role=user_to_save.role,
    )
    return {"message": "注册成功!", "user": back_user, "machine_uuid": machine_uuid}


async def get_user_in_db(
        phone: str = Form(...),
        password: str = Form(...),
        client_uuid: str = Form(...),
        user_code: str = Form("")
):
    # 解码phone和password
    phone = base64.b64decode(phone.encode('utf-8')).decode('utf-8')
    password = base64.b64decode(password.encode('utf-8')).decode('utf-8')
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT `id`,`user_code`,`username`,`phone`,`email`,`password_hashed`,`role` "
            "FROM `user_user` WHERE (`phone`=%s OR `user_code`=%s) AND `is_active`=1;",
            (phone, user_code)
        )
        user_dict = cursor.fetchone()
        if not user_dict:  # 数据库中没有查询到用户
            return None
        # 如果有用户,修改登录时间
        cursor.execute(
            "UPDATE `user_user` SET `recent_login`=%s WHERE `id`=%s;",
            (datetime.today(), user_dict["id"])
        )
        if not verify.verify_password(password, user_dict["password_hashed"]):  # 将查询到的密码验证
            return None
        # 如果密码验证通过,
        today_str = datetime.today().strftime("%Y-%m-%d")
        # 非超管和非运营查询当前用户是否能在这个客户端登录
        machine_uuid = encryption_uuid(client_uuid, user_dict["id"])  # 得到客户端uuid
        if user_dict["role"] not in ["superuser", "operator"]:
            cursor.execute(
                "SELECT userclient.id, userclient.user_id FROM user_user_client AS userclient "
                "INNER JOIN basic_client AS clienttb "
                "ON userclient.client_id=clienttb.id AND userclient.user_id=%s AND clienttb.machine_uuid=%s "
                "AND userclient.expire_date>%s AND clienttb.is_active=1;",
                (user_dict["id"], machine_uuid, today_str)
            )
            is_client_accessed = cursor.fetchone()
            if not is_client_accessed:
                raise HTTPException(status_code=403, detail="Can not login with the client.")
        user_dict["machine_uuid"] = machine_uuid
    return User(**user_dict)


@passport_router.post("/login/", response_model=JwtToken, summary="用户登录")
async def login_for_access_token(
        is_image_code_passed: bool = Depends(checked_image_code),
        user: User = Depends(get_user_in_db)
):
    if not is_image_code_passed:
        raise HTTPException(status_code=400, detail="Got an error image code.")
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password.")
    # 得到通过密码验证的用户,签发token证书
    access_token = verify.create_access_token(data={"user_id": user.id, "user_code": user.user_code})
    show_username = user.username if user.username else user.phone
    return {
        "message": "登录成功!",
        "show_username": show_username,
        "access_token": access_token,
        "token_type": "bearer",
        "machine_uuid": user.machine_uuid
    }


@passport_router.get("/image_code/", summary="图片验证码")
async def image_code(code_uuid: str):
    response = StreamingResponse(verify.generate_code_image(code_uuid))
    return response


@passport_router.get("/user/module-authenticate/", summary="用户当前的模块权限情况")
async def user_module_authority(
        user_token: str = Depends(verify.oauth2_scheme),
        query_user: int = Query(None)
):
    operate_user, _ = verify.decipher_user_token(user_token)
    if not operate_user:
        return {"message": "登录已过期了,重新登录再进行操作!", "user": {}, "modules": []}
    if query_user is None:
        query_user = operate_user   # 如果没有查询用户,就是自己查自己
    # 查询用户的模块权限
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id,username,user_code,role FROM user_user WHERE id=%s;", (query_user, )
        )
        user_info = cursor.fetchone()

        cursor.execute(
            "SELECT id,user_id,module_id,module_text,expire_date "
            "FROM user_user_module WHERE user_id=%s;", (user_info["id"])
        )
        data = cursor.fetchall()
    return {"message": "查询用户模块权限成功!", "user": user_info, "modules": data}


@passport_router.post("/user/module-authenticate/", summary="用户模块权限认证")
async def user_authenticate_module(
        module_item: ModuleItem = Body(...)
):
    if not module_item.user_token:
        raise HTTPException(status_code=403, detail="您还未登录,登录后在进行操作!")  # 403 -> reply.error() = 201
    user_id, user_code = verify.decipher_user_token(module_item.user_token)  # 解析用户信息
    if not user_id:
        raise HTTPException(status_code=403, detail="您登录已过期,请重新登录后再进行操作!")
    # 查询客户端类型和用户的身份信息
    with MySqlZ() as cursor:
        cursor.execute("SELECT `id`,is_manager,is_active FROM basic_client WHERE machine_uuid=%s;", (module_item.client_uuid, ))
        client_info = cursor.fetchone()
        cursor.execute("SELECT `id`,role,is_active FROM user_user WHERE id=%s;", (user_id, ))
        user_info = cursor.fetchone()

        if not client_info or not client_info["is_active"]:
            detail_message = "进入「{}」失败:\n无效客户端,无法进行这个操作!".format(module_item.module_text)
            raise HTTPException(status_code=401, detail=detail_message)            # 403 -> reply.error() = 204

        if not user_info or not user_info["is_active"]:
            detail_message = "进入「{}」失败:\n无效用户,无法进行这个操作!".format(module_item.module_text)
            raise HTTPException(status_code=401, detail=detail_message)

        if user_info["role"] in ["superuser", "operator"]:
            return {
                "message": "验证成功!",
                "authenticate": True,
                "module_id": module_item.module_id,
                "module_text": module_item.module_text,
            }

        if client_info["is_manager"] and module_item.module_id >= "0":
            return {
                "message": "验证成功!",
                "authenticate": True,
                "module_id": module_item.module_id,
                "module_text": module_item.module_text,
            }

        # 查询用户是否有权限进入相应模块
        today_str = datetime.today().strftime("%Y-%m-%d")
        cursor.execute(
            "SELECT `id`,user_id,module_id FROM user_user_module "
            "WHERE user_id=%s AND module_id=%s AND expire_date>%s;",
            (user_id, module_item.module_id, today_str)
        )
        is_accessed = cursor.fetchone()
        if not is_accessed:
            detail_message = "还没有「{}」的权限,请联系管理员进行开通!".format(module_item.module_text)
            raise HTTPException(status_code=401, detail=detail_message)
        else:
            return {
                "message": "验证成功!",
                "authenticate": True,
                "module_id": module_item.module_id,
                "module_text": module_item.module_text,
            }


@passport_router.put("/user/module-authenticate/", summary="修改用户的模块权限")
async def modify_module_authority(
        operate_token: str = Depends(verify.oauth2_scheme),
        modify_item: UserModuleAuthItem = Body(...)
):
    operate_user, _ = verify.decipher_user_token(operate_token)
    if not operate_user:
        raise HTTPException(status_code=401, detail="您登录过期了,重新登录后再操作!")
    # 验证expire_date
    try:
        datetime.strptime(modify_item.expire_date, '%Y-%m-%d')
    except Exception:
        raise HTTPException(status_code=400, detail="数据格式有误,修改失败!")
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT user_id,module_id FROM user_user_module WHERE module_id=%s AND user_id=%s;",
            (modify_item.module_id, modify_item.modify_user)
        )
        is_exist = cursor.fetchone()
        if is_exist:
            cursor.execute(
                "UPDATE user_user_module SET module_text=%(module_text)s,expire_date=%(expire_date)s "
                "WHERE user_id=%(modify_user)s AND module_id=%(module_id)s;",
                jsonable_encoder(modify_item)
            )
        else:
            cursor.execute(
                "INSERT INTO user_user_module (user_id, module_id, module_text, expire_date) "
                "VALUES (%(modify_user)s,%(module_id)s,%(module_text)s,%(expire_date)s);",
                jsonable_encoder(modify_item)
            )

    return {"message": "修改模块权限成功!"}


@passport_router.get("/user/client-authenticate/", summary="用户客户端登录权限情况")
async def user_module_authority(
        user_token: str = Depends(verify.oauth2_scheme),
        query_user: int = Query(...)
):
    operate_user, _ = verify.decipher_user_token(user_token)
    if not operate_user:
        return {"message": "登录已过期了,重新登录再进行操作!", "user": {}, "clients": []}
    # 查询用户的客户端登录权限
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id,username,user_code,role FROM user_user WHERE id=%s;", (query_user, )
        )
        user_info = cursor.fetchone()
        if not user_info:
            return {"message": "操作的用户不存在!", "user": {}, "clients": []}
        cursor.execute(
            "SELECT cliettb.id, cliettb.client_name,cliettb.machine_uuid,cliettb.is_manager,cliettb.is_active,uctb.expire_date "
            "FROM basic_client AS cliettb "
            "LEFT JOIN user_user_client AS uctb "
            "ON uctb.user_id=%s AND cliettb.id=uctb.client_id;",
            (user_info["id"], )
        )

        clients = cursor.fetchall()

    for client_item in clients:
        if user_info["role"] in ["superuser", "operator"]:  # 超级管理员和运营员都有权限登录
            client_item["expire_date"] = "3000-01-01"
    return {"message": "查询用户客户端登录权限成功!", "user": user_info, "clients": clients}


@passport_router.put("/user/client-authenticate/", summary="修改用户客户端登录权限")
async def modify_client_authority(
    operate_token: str = Depends(verify.oauth2_scheme),
    modify_item: UserClientAuthItem = Body(...)
):
    operate_user, _ = verify.decipher_user_token(operate_token)
    if not operate_user:
        raise HTTPException(status_code=401, detail="您登录过期了,重新登录后再操作!")
    # 验证expire_date
    try:
        datetime.strptime(modify_item.expire_date, '%Y-%m-%d')
    except Exception:
        raise HTTPException(status_code=400, detail="数据格式有误,修改失败!")
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT user_id,client_id FROM user_user_client WHERE client_id=%s AND user_id=%s;",
            (modify_item.client_id, modify_item.modify_user)
        )
        is_exist = cursor.fetchone()
        if is_exist:
            cursor.execute(
                "UPDATE user_user_client SET expire_date=%(expire_date)s "
                "WHERE user_id=%(modify_user)s AND client_id=%(client_id)s;",
                jsonable_encoder(modify_item)
            )
        else:
            # 查询client_uuid 如果后缀是0000则需要新增client表和可登录关联表的信息
            cursor.execute("SELECT id,machine_uuid,is_manager "
                           "FROM basic_client "
                           "WHERE id=%s;",
                           (modify_item.client_id, )
                           )
            client_obj = cursor.fetchone()
            raw_uuid_list = client_obj["machine_uuid"].rsplit("-", 1)
            if raw_uuid_list[1] == "0000":
                # 新增客户端信息
                # 生成用户使用的machine_id:
                machine_uuid = "{}-{}".format(raw_uuid_list[0], "%04d" % modify_item.modify_user)
                # 查询是否存在
                cursor.execute("SELECT id FROM basic_client WHERE machine_uuid=%s;", (machine_uuid,))
                real_user_client = cursor.fetchone()
                if real_user_client:  # 存在
                    real_client_id = real_user_client["id"]
                    # 更新可登录
                    cursor.execute(
                        "UPDATE user_user_client SET expire_date=%s "
                        "WHERE user_id=%s AND client_id=%s;",
                        (modify_item.expire_date, modify_item.modify_user, real_client_id)
                    )
                else:
                    # 增加可登录的客户端
                    cursor.execute(
                        "INSERT IGNORE INTO basic_client (machine_uuid,is_manager) "
                        "VALUES (%s,%s);",
                        (machine_uuid, client_obj["is_manager"])
                    )
                    real_client_id = cursor._instance.insert_id()
                    # 增加可登录信息库
                    cursor.execute(
                        "INSERT INTO user_user_client (user_id, client_id, expire_date) "
                        "VALUES (%s,%s,%s);",
                        (modify_item.modify_user, real_client_id, modify_item.expire_date)
                    )

            else:  # 不是为0000的客户端
                # 增加可登录信息
                cursor.execute(
                    "INSERT INTO user_user_client (user_id, client_id, expire_date) "
                    "VALUES (%s,%s,%s);",
                    (modify_item.modify_user, client_obj["id"], modify_item.expire_date)
                )
    return {"message": "修改用户客户端登录权限成功!"}


@passport_router.get("/user/variety-authenticate/", summary="用户当前品种权限情况")
async def user_variety_authority(
    user_token: str = Depends(verify.oauth2_scheme),
    query_user: int = Query(None)
):
    operate_user, _ = verify.decipher_user_token(user_token)
    if not operate_user:
        return {"message": "登录已过期了,重新登录再进行操作!", "user": {}, "varieties": []}
    if not query_user:   # 查询自己有权限的品种
        query_user = operate_user
    # 查询用户的品种权限
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id,username,user_code,role FROM user_user WHERE id=%s;", (query_user,)
        )
        user_info = cursor.fetchone()
        if not user_info:
            return {"message": "操作的用户不存在!", "user": {}, "varieties": []}

        cursor.execute(
            "SELECT varietytb.id, varietytb.variety_name,varietytb.variety_en,varietytb.exchange_lib,"
            "varietytb.is_active,varietytb.group_name,uvtb.expire_date "
            "FROM basic_variety AS varietytb "
            "LEFT JOIN user_user_variety AS uvtb "
            "ON uvtb.user_id=%s AND varietytb.id=uvtb.variety_id;",
            (user_info["id"],)
        )

        varieties = cursor.fetchall()
    for variety_item in varieties:
        variety_item['exchange_lib'] = ExchangeLibCN[variety_item['exchange_lib']]
        variety_item['group_name'] = VarietyGroupCN[variety_item['group_name']]
        if user_info["role"] in ["superuser", "operator"]:  # 超级管理员和运营员都有权限
            variety_item["expire_date"] = "3000-01-01"

    return {"message": "查询用户品种权限成功!", "user": user_info, "varieties": varieties}


@passport_router.put("/user/variety-authenticate/", summary="修改用户品种权限")
async def modify_client_authority(
    operate_token: str = Depends(verify.oauth2_scheme),
    modify_item: UserVarietyAuthItem = Body(...)
):
    operate_user, _ = verify.decipher_user_token(operate_token)
    if not operate_user:
        raise HTTPException(status_code=401, detail="您登录过期了,重新登录后再操作!")
    # 验证expire_date
    try:
        datetime.strptime(modify_item.expire_date, '%Y-%m-%d')
        if not re.match(r'^[A-Z]{1,2}$', modify_item.variety_en):
            raise ValueError("INVALID VARIETY.")
    except Exception:
        raise HTTPException(status_code=400, detail="数据格式有误,修改失败!")
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT user_id,variety_id FROM user_user_variety WHERE variety_id=%s AND user_id=%s;",
            (modify_item.variety_id, modify_item.modify_user)
        )
        is_exist = cursor.fetchone()
        if is_exist:
            cursor.execute(
                "UPDATE user_user_variety SET expire_date=%(expire_date)s "
                "WHERE user_id=%(modify_user)s AND variety_id=%(variety_id)s;",
                jsonable_encoder(modify_item)
            )
        else:
            cursor.execute(
                "INSERT INTO user_user_variety (user_id, variety_id, variety_en, expire_date) "
                "VALUES (%(modify_user)s,%(variety_id)s,%(variety_en)s,%(expire_date)s);",
                jsonable_encoder(modify_item)
            )

    return {"message": "修改用户品种权限成功!"}


@passport_router.get("/user/token-login/", summary="使用TOKEN进行自动登录")
async def user_token_logged(
        client: str = Query(..., min_length=36, max_length=36),
        token: str = Depends(verify.oauth2_scheme)
):
    user_id, user_code = verify.decipher_user_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="登录失败!Token Expired!")
    # 查询用户的有效与能否在此客户端登录
    with MySqlZ() as cursor:
        cursor.execute("SELECT `id`,role,username,note,is_active FROM user_user WHERE id=%s;", (user_id, ))
        user_info = cursor.fetchone()
        if not user_info:
            raise HTTPException(status_code=401, detail="登录失败!USER NOT FOUND!")

        today_str = datetime.today().strftime("%Y-%m-%d")
        # 1 创建今日在线的数据库
        cursor.execute(
            "SELECT `id`,online_date FROM user_user_online WHERE `user_id`=%s AND online_date=%s;",
            (user_info["id"], today_str)
        )
        is_today_online = cursor.fetchone()
        if not is_today_online:  # 今日还未登录
            cursor.execute(
                "INSERT INTO user_user_online (user_id,online_date,total_online) VALUES (%s,%s,%s);",
                (user_info["id"], today_str, 0)
            )
        # 2 非超管和运营查询当前用户是否能在这个客户端登录
        machine_uuid = encryption_uuid(client, user_id)
        if user_info["role"] not in ["superuser", "operator"]:
            cursor.execute("SELECT `id`,is_manager FROM basic_client WHERE machine_uuid=%s;", (machine_uuid,))
            client_info = cursor.fetchone()
            if not client_info:
                raise HTTPException(status_code=401, detail="登录失败!INVALID CLIENT!")
            cursor.execute(
                "SELECT userclient.id, userclient.user_id FROM user_user_client AS userclient "
                "INNER JOIN basic_client AS clienttb "
                "ON userclient.client_id=clienttb.id AND userclient.user_id=%s AND clienttb.machine_uuid=%s "
                "AND userclient.expire_date>%s;",
                (user_info["id"], machine_uuid, today_str)
            )
            is_client_accessed = cursor.fetchone()
            if not is_client_accessed:
                raise HTTPException(status_code=403, detail="Can not login with the client.")
    return {
        "message": "token登录成功!",
        "show_username": user_info["username"],
        "machine_uuid": machine_uuid
    }


@passport_router.post("/modify-password/", summary="用户修改密码")
async def modify_password(
        user_token: str = Depends(verify.oauth2_scheme),
        password_item: ModifyPasswordItem = Body(...)
):
    user_id, _ = verify.decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="UnAuthenticated!")
    if password_item.new_password != password_item.confirm_password:
        raise HTTPException(status_code=400, detail="两次密码输入不一致!")
    # 加密密码
    password_hashed = verify.get_password_hash(password_item.new_password)
    with MySqlZ() as cursor:
        # 验证旧密码
        cursor.execute("SELECT id,password_hashed FROM user_user WHERE id=%s;", (user_id,))
        user_info = cursor.fetchone()
        if not user_info:
            raise HTTPException(status_code=402, detail="原密码错误!")
        if not verify.verify_password(password_item.old_password, user_info["password_hashed"]):
            raise HTTPException(status_code=402, detail="原密码错误!")
        cursor.execute(
            "UPDATE user_user SET password_hashed=%s WHERE id=%s;",
            (password_hashed, user_id)
        )
    return {"message": "修改成功!"}


@passport_router.post("/reset-password/", summary="管理员重置用户密码")
async def reset_password(user_token: str = Depends(verify.oauth2_scheme), modify_user: int = Body(..., embed=True)):
    user_id, _ = verify.decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="UnAuthenticated!")
    with MySqlZ() as cursor:
        cursor.execute("SELECT id, role FROM user_user WHERE id=%s;", (user_id, ))
        operator_user = cursor.fetchone()
        if not operator_user:
            raise HTTPException(status_code=401, detail="UnAuthenticated!")
        if operator_user["role"] not in ["superuser", "operator"]:
            raise HTTPException(status_code=402, detail="没有权限进行这个操作!")
        # 重置用户密码
        password_hashed = verify.get_password_hash("123456")
        cursor.execute(
            "UPDATE user_user SET password_hashed=%s WHERE id=%s LIMIT 1;", (password_hashed, modify_user)
        )
        # 查询用户信息
        cursor.execute("SELECT id,user_code FROM user_user WHERE id=%s;", (modify_user, ))
        modify_user = cursor.fetchone()
        user_code = modify_user["user_code"] if modify_user else ''
    return {"message": "重置密码成功!", "user": {"user_code": user_code, "password": "123456"}}


# 发送邮件的后台任务
def send_email_verify_code(user_phone, user_email):
    receivers = [user_email]  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱
    # 生成验证码
    email_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    # 将验证码保存到redis
    value_key = '{}_email_code'.format(user_phone)
    with RedisZ() as r_conn:
        r_conn.set(value_key, email_code, 600)  # 10分钟有效
    mail_msg = """
            <p>您正在修改《瑞达期货研究院分析决策系统》的登录密码,如不是本人操作请忽略,并请尽快进入系统修改密码.</p>
            <p>本次验证码是:</p>
            <p style='font-size:17px;color:rgb(200,20,20)'>{}<p>
            """.format(email_code)
    message = MIMEText(mail_msg, 'html', 'utf-8')
    message['From'] = SYSTEM_EMAIL
    message['To'] = receivers[0]
    message['Subject'] = '<瑞达期货研究院分析决策系统>修改密码邮箱验证码'
    try:
        smtpObj = smtplib.SMTP(host='smtp.163.com')
        smtpObj.login(SYSTEM_EMAIL, SYSTEM_EMAIL_AUTH)
        smtpObj.sendmail(SYSTEM_EMAIL, receivers, message.as_string())
    except smtplib.SMTPException as e:
        logger.error("发送邮件错误!{}".format(e))


@passport_router.get("/email-code/", summary="用户发送邮箱验证码")
async def post_email_code(background_tasks: BackgroundTasks, phone: str = Query(..., regex=r'[1][3-9][0-9]{9}')):
    with MySqlZ() as cursor:
        cursor.execute("SELECT user_code,phone,email FROM user_user WHERE phone=%s;", (phone, ))
        user_obj = cursor.fetchone()
        if not user_obj:
            return {"message": "查无用户,请确认登录手机号正确", "status": 400}
        # 验证邮箱
        user_email = user_obj["email"]
        if not re.match(r'^(\w+\.?)*\w+@(?:\w+\.)\w+$', user_email):
            return {"message": "预留邮箱格式错误.发送验证码失败", "status": 400}
        background_tasks.add_task(send_email_verify_code, phone, user_email)
        return {"message": "验证码已发送!", "status": 200}


@passport_router.post("/reset-password/email/", summary="用户通过邮箱重置密码")
async def reset_password_email(reset_item: ResetPasswordEmail):
    # 验证手机号
    if not re.match(r"^[13456789]{3}[0-9]{8}$", reset_item.user_phone):
        raise HTTPException(status_code=400, detail="手机号格式错误!")
    # 验证新旧秘密
    if reset_item.new_password != reset_item.confirm_password:
        raise HTTPException(status_code=400, detail="两次输入的密码不一致!")
    if len(reset_item.new_password) < 6 or len(reset_item.new_password) > 20:
        raise HTTPException(status_code=400, detail="密码为6-20位的字母数字联合")
    # 通过phone查询保存的邮箱验证码
    value_key = '{}_email_code'.format(reset_item.user_phone)
    with RedisZ() as r_conn:
        real_email_code = r_conn.get(value_key)
    if not real_email_code or real_email_code != reset_item.email_code:
        raise HTTPException(status_code=400, detail="邮箱验证码有误")
    # 修改用户的新密码
    password_hash = verify.get_password_hash(reset_item.new_password)
    with MySqlZ() as cursor:
        cursor.execute(
            "UPDATE user_user SET password_hashed=%s WHERE phone=%s;",
            (password_hash, reset_item.user_phone)
        )
    return {"message": "密码重置成功!请登录.."}













@passport_router.post("/login/file/", summary="测试接口,上传文件")
async def login_file(
        file_key: UploadFile = File(...),
):
    print(file_key.filename)
    return {"message": "上传文件"}


@passport_router.get("/token_login/", summary="使用token进行登录")
async def login_status_keeping(
        is_logged: bool = Depends(verify.is_user_logged_in),
):
    print("用户登录情况:", is_logged)
    return {"message": "用户登录"}
