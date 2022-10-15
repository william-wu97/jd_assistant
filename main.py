# coding=UTF-8
import requests
import threading
import jd_account
import jd_assistant
from log import logger
from util import init_config, get_config, list_to_json, parse_sku_id

if __name__ == '__main__':
    logger.info('Power By JACK')
    init_config()
    if not jd_account.load_cookies():
        jd_account.login_by_qr_code()
    config_list = get_config()
    account_list = jd_account.get_account()
    config_json = list_to_json(config_list)
    area_id = config_json.get('area_id', '')
    area = config_json.get('area', '')
    sku_ids = config_json.get('sku_ids', '')
    buy_time = config_json.get('buy_time', '')
    mode = config_json.get('mode', '')
    if not (area_id and sku_ids and buy_time and mode):
        logger.info('请完善配置文件')
        input('\n')
    else:
        if mode in ('1', '2', '3', '4', '5'):
            items_dict = parse_sku_id(sku_ids)
            sku_id = list(items_dict.keys())[0]
            num = list(items_dict.values())[0]
            get_time = jd_assistant.get_buy_time(sku_id)
            buy_time = get_time if get_time else buy_time
            session_list = []
            for account in account_list:
                cookies = jd_account.string_to_cookies(account[1])
                session = requests.session()
                session.headers = jd_assistant.headers
                session.cookies = cookies
                if jd_account.check_login(account[0], session):
                    jd_account.set_address(session, area)
                    if mode == '1':
                        threading.Thread(target=jd_assistant.cart_seckill_one_by_time,
                                         args=(session, sku_ids, buy_time)).start()
                    if mode == '2':
                        for sku_id, num in items_dict.items():
                            jd_assistant.make_reserve(session, sku_id)
                            threading.Thread(target=jd_assistant.presale_seckill_by_time,
                                             args=(session, sku_id, num, buy_time)).start()
                    if mode == '3':
                        for sku_id, num in items_dict.items():
                            jd_assistant.make_reserve(session, sku_id)
                            threading.Thread(target=jd_assistant.exec_seckill_by_time,
                                             args=(session, sku_id, num, buy_time)).start()
                    if mode == '4':
                        session_list.append(session)
                    if mode == '5':
                        jd_assistant.get_order_list(session)
            if mode == '4':
                jd_assistant.buy_item_in_stock(session_list, sku_ids, area_id)
        else:
            logger.info('无此模式')
        input('\n')
