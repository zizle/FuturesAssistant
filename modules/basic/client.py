# _*_ coding:utf-8 _*_
# @File  : basic.py
# @Time  : 2020-08-31 8:46
# @Author: zizle
from fastapi import APIRouter, Body, Query, HTTPException, Depends
from fastapi.encoders import jsonable_encoder
from utils.client import encryption_uuid
from db.mysql_z import MySqlZ
from utils.verify import oauth2_scheme, decipher_user_token
from .validate_models import ClientItem, ModifyClient

client_router = APIRouter()


@client_router.post("/client/", summary="添加一个客户端")
async def add_new_client(client: ClientItem = Body(...)):
    client.machine_uuid = encryption_uuid(client.machine_uuid)
    client_dict = jsonable_encoder(client)
    with MySqlZ() as cursor:
        cursor.execute("SELECT `id`,`client_name` FROM `basic_client` WHERE `machine_uuid`=%s;", client.machine_uuid)
        client_info = cursor.fetchone()
        if not client_info:  # 客户端不存在
            cursor.execute(
                "INSERT INTO `basic_client` "
                "(client_name,machine_uuid,is_manager) "
                "VALUES (%(client_name)s,%(machine_uuid)s,%(is_manager)s);",
                client_dict
            )
    return {"message": "新增客户端成功!", "client_uuid": client.machine_uuid}


@client_router.get("/client/", summary="获取客户端列表")
async def get_clients(c_type: str = Query("normal")):
    if c_type not in ["normal", "manager"]:
        raise HTTPException(status_code=400, detail="type error.")
    is_manager = 1 if c_type == "manager" else 0
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id,DATE_FORMAT(join_time,'%%Y-%%m-%%d') AS join_date,client_name,"
            "machine_uuid,is_manager,is_active "
            "FROM basic_client WHERE is_manager=%s;",
            (is_manager, )
        )
        clients = cursor.fetchall()

    return {"message": "查询成功!", "clients": clients}


@client_router.get("/client/{client_uuid}/", summary="通过uuid获取client")
async def get_client_with_uuid(client_uuid: str):
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id,DATE_FORMAT(join_time,'%%Y-%%m-%%d') AS join_date,client_name,"
            "machine_uuid,is_manager,is_active "
            "FROM basic_client WHERE machine_uuid=%s;",
            (client_uuid, )
        )
        clients = cursor.fetchall()
    return {"message": "查询成功!", "clients": clients}


@client_router.put("/client/{client_id}/", summary="修改客户端信息")
async def modify_client(
        client_id: int,
        client: ModifyClient = Body(...),
        user_token: str = Depends(oauth2_scheme)
):
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Unknown User")
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT id,role FROM user_user WHERE id=%s;", (user_id, )
        )
        operator = cursor.fetchone()
        if not operator or operator["role"] not in ["superuser", "operator"]:
            raise HTTPException(status_code=401, detail="Unknown User")

        # 验证is_active
        if client.is_active not in [0, 1]:
            raise HTTPException(status_code=400, detail="Error Params")
        # 验证is_manager
        if client.is_manager not in [0, 1]:
            raise HTTPException(status_code=400, detail="Error Params")
        if client.client_id != client_id:
            raise HTTPException(status_code=400, detail="Client Error")
        # 修改客户端信息
        cursor.execute(
            "UPDATE basic_client SET client_name=%(client_name)s,is_manager=%(is_manager)s,"
            "is_active=%(is_active)s WHERE id=%(client_id)s;",
            jsonable_encoder(client)
        )
    return {"message": "修改{}客户端信息成功!".format(client.client_uuid)}




