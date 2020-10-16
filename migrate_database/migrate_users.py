# _*_ coding:utf-8 _*_
# @File  : migrate_users.py
# @Time  : 2020-09-16 14:21
# @Author: zizle
""" 迁移用户数据 """
import random
from uuid import uuid4
from old_database import OldSqlZ
from db.mysql_z import MySqlZ
ROLE_DICT = {
    2: "operator",
    4: "research"
}


def generate_user_code():
    uuid = ''.join(str(uuid4()).split("-"))
    return "user_" + ''.join([random.choice(uuid) for _ in range(15)])


with OldSqlZ() as cursor:
    cursor.execute(
        "SELECT * "
        "FROM info_user;"
    )
    old_users = cursor.fetchall()

to_saves = list()
for user_item in old_users:
    if user_item["id"] in [1, 19]:
        continue
    save_item = {
        "join_time": user_item["join_time"],
        "recent_login": user_item["update_time"],
        "user_code": generate_user_code(),
        "username": user_item["username"],
        "phone": user_item["phone"],
        "email": user_item["email"],
        "password_hashed": user_item["password"],
        "role": ROLE_DICT.get(user_item["role_num"]),
        "note": user_item["note"]
    }
    to_saves.append(save_item)

with MySqlZ() as cursor:
    cursor.executemany(
        "INSERT INTO user_user (join_time,recent_login,user_code,username,phone,email,password_hashed,"
        "role,note) VALUES (%(join_time)s,%(recent_login)s,%(user_code)s,"
        "%(username)s,%(phone)s,%(email)s,%(password_hashed)s,%(role)s,%(note)s);",
        to_saves
    )
