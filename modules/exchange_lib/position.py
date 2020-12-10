# _*_ coding:utf-8 _*_
# @File  : position.py
# @Time  : 2020-08-21 12:55
# @Author: zizle

""" 持仓相关 """
from datetime import datetime, timedelta
from fastapi import APIRouter, Query, Depends, Body
from pandas import DataFrame, pivot_table, concat
from db.mysql_z import ExchangeLibDB, MySqlZ
from utils.constant import VARIETY_ZH, VARIETY_CODES_ALL
from utils.verify import oauth2_scheme, decipher_user_token

position_router = APIRouter()


DCE_VARIETY_EN = ['A', 'B', 'C', 'CS', 'EB', 'EG', 'I', 'J', 'JD', 'JM', 'L', 'M', 'P', 'PG', 'PP', 'RR', 'V', 'Y']
CZCE_VARIETY_EN = ['AP', 'CF', 'CJ', 'CY', 'FG', 'JR', 'LR', 'MA', 'OI', 'PF', 'PM', 'RI', 'RM', 'RS', 'SA', 'SF', 'SM',
                   'SR', 'TA', 'UR', 'WH', 'ZC']
SHFE_VARIETY_EN = ['AG', 'AL', 'AU', 'BU', 'CU', 'FU', 'HC', 'LU', 'NI', 'NR', 'PB', 'RB',
                   'RU', 'SN', 'SP', 'SS', 'ZN']
CFFEX_VARIETY_EN = ['IC', 'IF', 'IH', 'T', 'TF', 'TS']


def pivot_data_frame(source_df, exchange_lib):
    """ 透视转表数据 """
    source_df["net_position"] = source_df["net_position"].astype(int)
    pivot_df = pivot_table(source_df, index=["variety_en"], columns=["date"])
    # 检测不存在的品种插入插入行,数据为nan
    if exchange_lib == 'dce':
        pivot_df = pivot_df.reindex(DCE_VARIETY_EN, axis="rows")
    elif exchange_lib == 'czce':
        pivot_df = pivot_df.reindex(CZCE_VARIETY_EN, axis="rows")
    elif exchange_lib == 'shfe':
        pivot_df = pivot_df.reindex(SHFE_VARIETY_EN, axis="rows")
    elif exchange_lib == 'cffex':
        pivot_df = pivot_df.reindex(CFFEX_VARIETY_EN, axis="rows")
    else:
        pass
    return pivot_df


def get_variety_zh(variety_en):
    """ 获取交易代码的对应中文 """
    return VARIETY_ZH.get(variety_en, variety_en)

# 速度极慢，预计废弃
@position_router.get('/position/all-variety/', summary='全品种净持仓数据')
async def all_variety_net_position(interval_days: int = Query(1)):
    # 获取当前日期及45天前
    current_date = datetime.today()
    pre_date = current_date + timedelta(days=-45)
    start_date = pre_date.strftime('%Y%m%d')
    end_date = current_date.strftime('%Y%m%d')
    with ExchangeLibDB() as cursor:
        # 查询大商所的品种净持仓
        cursor.execute(
            "select `date`,variety_en,(sum(long_position) - sum(short_position)) as net_position "
            "from dce_rank "
            "where date<=%s and date>=%s and `rank`>=1 and `rank`<=20 "
            "group by `date`,variety_en;",
            (end_date, start_date)
        )
        dce_net_positions = cursor.fetchall()

        # 查询郑商所的品种净持仓
        cursor.execute(
            "select `date`,variety_en,(sum(long_position) - sum(short_position)) as net_position "
            "from czce_rank "
            "where date<=%s and date>=%s and `rank`>=1 and `rank`<=20  and variety_en=contract "
            "group by `date`,variety_en;",
            (end_date, start_date)
        )
        czce_net_positions = cursor.fetchall()

        # 查询上期所的品种净持仓
        cursor.execute(
            "select `date`,variety_en,(sum(long_position) - sum(short_position)) as net_position "
            "from shfe_rank "
            "where date<=%s and date>=%s and `rank`>=1 and `rank`<=20 "
            "group by `date`,variety_en;",
            (end_date, start_date)
        )
        shfe_net_positions = cursor.fetchall()

        # 查询中金所的品种净持仓
        cursor.execute(
            "select `date`,variety_en,(sum(long_position) - sum(short_position)) as net_position "
            "from cffex_rank "
            "where date<=%s and date>=%s and `rank`>=1 and `rank`<=20 "
            "group by `date`,variety_en;",
            (end_date, start_date)
        )
        cffex_net_positions = cursor.fetchall()

    # 处理各交易所的数据
    dce_df = DataFrame(dce_net_positions)
    czce_df = DataFrame(czce_net_positions)
    shfe_df = DataFrame(shfe_net_positions)
    cffex_df = DataFrame(cffex_net_positions)

    all_variety_df = concat(
        [pivot_data_frame(dce_df, 'dce'), pivot_data_frame(czce_df, 'czce'), pivot_data_frame(shfe_df, 'shfe'), pivot_data_frame(cffex_df, 'cffex')]
    )
    # 倒置列顺序
    all_variety_df = all_variety_df.iloc[:, ::-1]
    # 间隔取数(目标数据:今日,前1天,前interval_days * index 天)
    columns_list = [col for col in range(all_variety_df.shape[1])]
    extra_columns = columns_list[::interval_days]
    if interval_days != 1:
        extra_columns.insert(1, 1)
    # split_df = all_variety_df.iloc[:, ::interval_days]
    split_df = all_variety_df.iloc[:, extra_columns]
    # 整理表头
    split_df.columns = split_df.columns.droplevel(0)
    split_df = split_df.reset_index()
    split_df = split_df.fillna(0)
    # 处理顺序(按字母排序)
    split_df.sort_values(by='variety_en', inplace=True)
    # 增加中文列
    split_df["variety_zh"] = split_df["variety_en"].apply(get_variety_zh)
    data_dict = split_df.to_dict(orient='records')
    header_keys = split_df.columns.values.tolist()
    header_keys.remove("variety_zh")  # 删除中文标签
    header_keys[0] = "variety_zh"  # 第一个改为中文
    final_data = dict()
    for item in data_dict:
        final_data[item['variety_en']] = item
    return {"message": "查询全品种净持仓数据成功!", "data": final_data, 'header_keys': header_keys}


""" 生成20净持仓变化的数据 """


# 查询当前日期的前一天数据(这里要求原数据库必须至少有一条数据,且日期间隔不能超过mysql最大连接数)
def query_preday(query_date):
    query_date = (query_date + timedelta(days=-1)).strftime("%Y%m%d")
    with ExchangeLibDB() as ex_cursor:
        ex_cursor.execute(
            "SELECT variety_en,long_position,short_position,net_position "
            "FROM zero_rank_position WHERE `date`=%s;", (query_date, )
        )
        date_data = ex_cursor.fetchall()
        if not date_data:
            return query_preday(datetime.strptime(query_date, "%Y%m%d"))
        return date_data


@position_router.post("/rank-position/", summary='生成净持仓数据')
async def generate_rank_position(option_day: str = Body(..., embed=True), user_token: str = Depends(oauth2_scheme)):
    # 验证日期格式
    try:
        option_day = datetime.strptime(option_day, "%Y%m%d")
    except Exception:
        return {"message": "日期格式有误!"}
    user_id, _ = decipher_user_token(user_token)
    if not user_id:
        return {"message": "暂无权限操作或登录过期"}
    # 验证用户身份
    with MySqlZ() as m_cursor:
        m_cursor.execute("SELECT id,role FROM user_user WHERE id=%s;", (user_id, ))
        user_info = m_cursor.fetchone()
        if not user_info or user_info["role"] not in ["superuser", "operator"]:
            return {"message": "暂无权限操作"}
    # 进行数据生成
    # 获取当前数据库中前一天的数据
    pre_data = query_preday(option_day)
    # 转为dic
    pre_dict = {}
    for pre_item in pre_data:
        pre_dict[pre_item["variety_en"]] = pre_item
    query_date = option_day.strftime("%Y%m%d")
    # 查询四大交易所数据并进行生成
    with ExchangeLibDB() as cursor:
        # 查询中金所品种持仓
        cursor.execute(
            "select `date`,variety_en,"
            "sum(long_position) as long_position,sum(short_position) as short_position "
            "from cffex_rank "
            "where date=%s and `rank`>=1 and `rank`<=20 "
            "group by variety_en;",
            (query_date, )
        )
        cffex_positions = cursor.fetchall()
        # 查询郑商所品种持仓
        cursor.execute(
            "select `date`,variety_en,"
            "sum(long_position) as long_position,sum(short_position) as short_position "
            "from czce_rank "
            "where date=%s and `rank`>=1 and `rank`<=20 and variety_en=contract "
            "group by variety_en;",
            (query_date, )
        )
        czce_positions = cursor.fetchall()
        # 查询大商所品种持仓
        cursor.execute(
            "select `date`,variety_en,"
            "sum(long_position) as long_position,sum(short_position) as short_position "
            "from dce_rank "
            "where date=%s and `rank`>=1 and `rank`<=20 "
            "group by variety_en;",
            (query_date,)
        )
        dce_positions = cursor.fetchall()
        # 查询上期所持仓
        cursor.execute(
            "select `date`,variety_en,"
            "sum(long_position) as long_position,sum(short_position) as short_position "
            "from shfe_rank "
            "where date=%s and `rank`>=1 and `rank`<=20 "
            "group by variety_en;",
            (query_date,)
        )
        shfe_positions = cursor.fetchall()

        # 合并以上查询的结果
        save_items = list(cffex_positions) + list(czce_positions) + list(dce_positions) + list(shfe_positions)
        # 转换数据类型
        for item in save_items:
            item["long_position"] = int(item["long_position"])
            item["short_position"] = int(item["short_position"])
            item["net_position"] = item["long_position"] - item["short_position"]
            pre_day = pre_dict.get(item["variety_en"])
            if pre_day:
                item["long_position_increase"] = item["long_position"] - pre_day["long_position"]
                item["short_position_increase"] = item["short_position"] - pre_day["short_position"]
                item["net_position_increase"] = item["net_position"] - pre_day["net_position"]
            else:
                item["long_position_increase"] = item["long_position"]
                item["short_position_increase"] = item["short_position"]
                item["net_position_increase"] = item["net_position"]
        # 将items保存入库
        if not save_items:
            return {"message": "没有查询到今日的持仓数据,无生成结果"}
        count = cursor.executemany(
            "INSERT IGNORE INTO zero_rank_position (`date`,variety_en,"
            "long_position,long_position_increase,short_position,short_position_increase,"
            "net_position,net_position_increase) "
            "VALUES (%(date)s,%(variety_en)s,"
            "%(long_position)s,%(long_position_increase)s,%(short_position)s,%(short_position_increase)s,"
            "%(net_position)s,%(net_position_increase)s);",
            save_items
        )
    return {"message": "保存{}排名持仓和数据成功!数量{}个".format(query_date, count)}


@position_router.get("/rank-position/all-variety/", summary='查询全品种近35天净持仓数据')
def get_rank_position(interval_days: int = Query(1)):
    # 获取当前日期及35天前
    current_date = datetime.today()
    pre_date = current_date + timedelta(days=-35)
    start_date = pre_date.strftime('%Y%m%d')
    end_date = current_date.strftime('%Y%m%d')
    with ExchangeLibDB() as ex_cursor:
        ex_cursor.execute(
            "SELECT `date`,variety_en,net_position FROM zero_rank_position "
            "WHERE `date`>=%s AND `date`<=%s;",
            (start_date, end_date)
        )
        all_data = ex_cursor.fetchall()
    if not all_data:
        return {"message": "查询全品种净持仓数据成功!", "data": [], 'header_keys': {}}
    # 整成pandas
    all_variety_df = DataFrame(all_data)
    # 表透视
    all_variety_df = pivot_table(all_variety_df, index=["variety_en"], columns=["date"])
    # 处理品种顺序
    all_variety_df = all_variety_df.reindex(VARIETY_CODES_ALL, axis='rows')
    # 倒置列顺序
    all_variety_df = all_variety_df.iloc[:, ::-1]
    # 间隔取数(目标数据:今日,前1天,前interval_days * index 天)
    columns_list = [col for col in range(all_variety_df.shape[1])]
    extra_columns = columns_list[::interval_days]
    if interval_days != 1:
        extra_columns.insert(1, 1)
    # 取数
    split_df = all_variety_df.iloc[:, extra_columns]
    # 整理表头
    split_df.columns = split_df.columns.droplevel(0)
    split_df = split_df.reset_index()
    split_df = split_df.fillna(0)
    # 处理顺序(按字母排序)
    split_df.sort_values(by='variety_en', inplace=True)
    # 增加中文列
    split_df["variety_zh"] = split_df["variety_en"].apply(get_variety_zh)
    data_dict = split_df.to_dict(orient='records')
    header_keys = split_df.columns.values.tolist()
    header_keys.remove("variety_zh")  # 删除中文标签
    header_keys[0] = "variety_zh"  # 第一个改为中文
    final_data = dict()
    for item in data_dict:
        final_data[item['variety_en']] = item
    return {"message": "查询全品种净持仓数据成功!", "data": final_data, 'header_keys': header_keys}


@position_router.get('/rank-position/', summary='查询品种净持仓数据')
def rank_net_position(variety: str = Query(0), day_count: int = Query(30)):
    # 获取日期
    current_date = datetime.today()
    pre_date = current_date + timedelta(days=-day_count)
    start_date = pre_date.strftime('%Y%m%d')
    end_date = current_date.strftime('%Y%m%d')
    # 查询
    with ExchangeLibDB() as ex_cursor:
        ex_cursor.execute(
            "SELECT `date`,variety_en,long_position,short_position,net_position,"
            "net_position_increase FROM zero_rank_position "
            "WHERE `date`>=%s AND `date`<=%s AND IF('0'=%s,TRUE,variety_en=%s);",
            (start_date, end_date, variety, variety)
        )
        all_data = ex_cursor.fetchall()
    if not all_data:
        return {"message": "查询全品种净持仓数据成功!", "data": [], 'header_keys': {}}
    # 整成pandas
    all_variety_df = DataFrame(all_data)
    # 增加中文列
    all_variety_df["variety_zh"] = all_variety_df["variety_en"].apply(get_variety_zh)
    data_list = all_variety_df.to_dict(orient='records')
    # final_data = dict()
    # for item in data_dict:
    #     final_data[item['variety_en']] = item
    return {"message": "查询全品种净持仓数据成功!", "data": data_list}
