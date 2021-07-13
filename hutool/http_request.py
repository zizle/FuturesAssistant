# _*_ coding:utf-8 _*_
# @File  : http_request.py
# @Time  : 2021-04-16 13:13
# @Author: zizle
import json
import random
import requests
from logger import logger
from .constants import USER_AGENTS


class HttpRequest(object):

    @staticmethod
    def get(url, params=None, parser_json=False, **kwargs):
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        try:
            r = requests.get(url=url, params=params, headers=headers, **kwargs)
            content = r.text
            if parser_json:
                content = json.loads(content)
        except Exception as e:
            logger.error(f'Get {url} ERROR: {e}')
            return {} if parser_json else ''
        return content
