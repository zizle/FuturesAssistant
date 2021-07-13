# _*_ coding:utf-8 _*_
# @File  : security.py
# @Time  : 2021-04-01 13:14
# @Author: zizle

import os
import hashlib
import time
import random
import base64
import Crypto.Cipher.PKCS1_v1_5
import Crypto.PublicKey.RSA
import Crypto.Random
from io import BytesIO
from jose import jwt, JWTError
from PIL import Image, ImageDraw, ImageFont
from passlib.context import CryptContext
from configs import TOKEN_EXPIRES, APP_DIR

# deprecated="auto"文档解释：自动将列表中除第一个哈希程序外的所有哈希程序标记为已弃用(2.0版默认值)。(不懂什么意思)
pwd_context = CryptContext(schemes=['bcrypt'], deprecated="auto")

SECRET_KEY = 'n&AdCG^PBtXhL#NKvUSo4OJ98)2x#x4CV0F2LmaziTsA4$VX'


def cipher_user_password(password):  # 哈希加密用户密码
    return pwd_context.hash(password)


def decipher_user_password(password, hash_password):  # 比对用户密码
    return pwd_context.verify(password, hash_password)


def create_access_token(data: dict, expire_seconds: int = TOKEN_EXPIRES):  # 生成json web token
    to_encode = data.copy()
    expire = time.time() + expire_seconds
    to_encode.update({"exp": expire})
    encode_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
    return encode_jwt


def decrypt_access_token(token):  # 解密 json web token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms='HS256')
    except JWTError:
        return None
    return payload


def rsa_encrypt(message, key_tuple):  # 使用公钥进行加密
    public_file = os.path.join(APP_DIR, f'ini/public{key_tuple}.pem')
    with open(public_file, "rb") as x:
        b = x.read()
    cipher_public = Crypto.Cipher.PKCS1_v1_5.new(Crypto.PublicKey.RSA.importKey(b))
    cipher_text = cipher_public.encrypt(message.encode('utf8'))  # 使用公钥进行加密
    return base64.b64encode(cipher_text).decode('utf8')


def rsa_decrypt(secret_message, key_tuple):  # 使用私钥进行解密
    try:
        private_file = os.path.join(APP_DIR, f'ini/private{key_tuple}.pem')
        with open(private_file, "rb") as x:
            a = x.read()
        data = base64.b64decode(secret_message)
        # 如果私钥有密码 则使用相应密码 Crypto.PublicKey.RSA.importKey(a, password)
        cipher_private = Crypto.Cipher.PKCS1_v1_5.new(Crypto.PublicKey.RSA.importKey(a))
        text = cipher_private.decrypt(data, None).decode('utf8')  # 使用私钥进行解密
    except Exception as e:
        return ''
    else:
        return text


def get_random_color():
    return random.randint(0, 240), random.randint(0, 240), random.randint(0, 240)  # 随机颜色


def generate_image_code():  # 生成图片验证码
    img_obj = Image.new(mode='RGB', size=(90, 30), color=(240, 240, 240))  # 生成一个图片对象
    draw_obj = ImageDraw.Draw(img_obj)  # 生成一个图片画笔对象
    ttf_path = os.path.join(APP_DIR, "ttf/KumoFont.ttf")  # 加载字体文件， 得到一个字体对象
    font_obj = ImageFont.truetype(ttf_path, 28)

    tmp_list = []  # 生成随机字符串并写到图片上
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
    return buf, text


def get_md5_hash_string(message: str, salts=None):  # md5哈希
    if salts is None:
        salts = list()
    hash_ = hashlib.md5(message.encode('utf8'))
    for salt_str in salts:
        hash_.update(salt_str.encode('utf8'))
    return hash_.hexdigest()

