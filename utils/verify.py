# _*_ coding:utf-8 _*_
# @File  : verify.py
# @Time  : 2020-08-31 8:25
# @Author: zizle
import os
import random
import time
from hashlib import md5
from typing import Optional
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.exceptions import HTTPException
from jose import jwt, JWTError
from db.redis_z import RedisZ
from db.mysql_z import MySqlZ
from configs import APP_DIR
from uuid import uuid4
from passlib.context import CryptContext
from configs import SECRET_KEY, JWT_EXPIRE_SECONDS

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def generate_code_image(redis_key):
    """ 生成四位数验证码,存入Redis """
    def get_random_color():  # 获取随机颜色的函数
        return random.randint(0, 240), random.randint(0, 240), random.randint(0, 240)

    # 生成一个图片对象
    img_obj = Image.new(
        'RGB',
        (90, 30),
        (240, 240, 240)
    )
    # 在生成的图片上写字符
    # 生成一个图片画笔对象
    draw_obj = ImageDraw.Draw(img_obj)
    # 加载字体文件， 得到一个字体对象
    ttf_path = os.path.join(APP_DIR, "ttf/KumoFont.ttf")
    font_obj = ImageFont.truetype(ttf_path, 28)
    # 开始生成随机字符串并且写到图片上
    tmp_list = []
    for i in range(4):
        # u = chr(random.randint(65, 90))  # 生成大写字母
        # l = chr(random.randint(97, 122))  # 生成小写字母
        n = str(random.randint(0, 9))  # 生成数字，注意要转换成字符串类型
        # tmp = random.choice([u, l, n])
        # tmp_list.append(tmp)

        tmp_list.append(n)  # 只生成数字

        # draw_obj.text((10 + 15 * i, 0), tmp, fill=get_random_color(), font=font_obj)  # 20（首字符左间距） + 20*i 字符的间距
        draw_obj.text((10 + 15 * i, 0), n, fill=get_random_color(), font=font_obj)  # 20（首字符左间距） + 20*i 字符的间距
    # 加干扰线
    width = 80  # 图片宽度（防止越界）
    height = 30
    for i in range(4):
        x1 = random.randint(0, width)
        x2 = random.randint(0, width)
        y1 = random.randint(0, height)
        y2 = random.randint(0, height)
        draw_obj.line((x1, y1, x2, y2), fill=get_random_color())
    # 加干扰点
    for i in range(25):
        draw_obj.point((random.randint(0, width), random.randint(0, height)), fill=get_random_color())
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw_obj.arc((x, y, x + 4, y + 4), 0, 90, fill=get_random_color())
    # 获得一个缓存区
    buf = BytesIO()
    # 将图片保存到缓存区
    img_obj.save(buf, 'png')
    buf.seek(0)
    # 将验证码保存到redis
    text = ''.join(tmp_list)
    with RedisZ() as r:
        r.set(name=redis_key, value=text, ex=120)
    return buf


def verify_password(plain_password, hashed_password):
    return get_password_hash(plain_password) == hashed_password


def get_password_hash(password):
    hasher = md5()
    hasher.update(password.encode('utf-8'))
    hasher.update(SECRET_KEY.encode('utf-8'))
    return hasher.hexdigest()


def generate_user_unique_code():
    uuid = ''.join(str(uuid4()).split("-"))
    return "user_" + ''.join([random.choice(uuid) for _ in range(15)])


def create_access_token(data: dict, expire_seconds: Optional[int] = JWT_EXPIRE_SECONDS):
    """ 创建JWT """
    to_encode = data.copy()
    expire = time.time() + expire_seconds
    to_encode.update({"exp": expire})
    encode_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encode_jwt


def is_active_user(user_code: str):
    """ 使用unique_code 从数据库中获取用户 """
    with MySqlZ() as cursor:
        cursor.execute(
            "SELECT `id`,`user_code` FROM `user_user` WHERE `user_code`=%s AND `is_active`=1;",
            (user_code, )
        )
        user_dict = cursor.fetchone()
    if user_dict:
        return True
    else:
        return False


def decipher_user_token(token):
    """ 解析token """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms='HS256')
        user_id: int = payload.get("user_id")  # `user_code`与生成时的对应
        user_code: str = payload.get("user_code")  # `user_code`与生成时的对应
        if user_code is None:
            raise JWTError
    except JWTError:
        return None, None
    return user_id, user_code


async def is_user_logged_in(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id, user_code = decipher_user_token(token)
    if not user_code:
        raise credentials_exception
    # 从数据库中获取用户
    if is_active_user(user_code):
        return True
    else:
        return False
