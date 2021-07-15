# _*_ coding:utf-8 _*_
# @File  : client_op.py
# @Time  : 2021-06-10 15:05
# @Author: zizle


from fastapi import APIRouter, Depends, Query
from db import FAConnection
from interfaces.depends import admin_logged_require
from status import r_status

op_client_api = APIRouter()


@op_client_api.get('/client/', summary='分页获取客户端列表')
async def get_clients(person: dict = Depends(admin_logged_require), page: int = Query(..., ge=1),
                      page_size: int = Query(..., ge=20, le=100)):
    db = RuiZyDBConnection(conn_name='Query Clients')
    start_record = (page - 1) * page_size
    offset_record = page_size
    query_sql = 'SELECT SQL_CALC_FOUND_ROWS id,create_time,update_time,client_name,disk,board,client_code,category,' \
                'is_active ' \
                'FROM sys_client ORDER BY update_time DESC LIMIT %s,%s;'
    records = db.query(query_sql, [start_record, offset_record], keep_conn=True)
    total_obj = db.query('SELECT FOUND_ROWS() AS total;', fetchone=True)
    total_count = total_obj[0]['total'] if total_obj else 0  # 当前总数量
    for item in records:
        item['create_time'] = item['create_time'].strftime('%Y-%m-%d %H:%M:%S')
        item['update_time'] = item['update_time'].strftime('%Y-%m-%d %H:%M:%S')
        item['category_name'] = CLIENT['CATEGORY'].get(item['category'], '未知')
    return {'code': r_status.SUCCESS, 'message': '查询客户端列表成功!', 'data': records, 'page': page,
            'page_size': page_size, 'total_count': total_count}
