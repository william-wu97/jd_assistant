# coding=UTF-8
import re
import json
import time
import datetime
import requests
import threading
import jd_account
from bs4 import BeautifulSoup
from log import logger
from util import parse_json, parse_sku_id, get_tag_value, parse_items_dict, save_msg

timeout = 2
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'}
eid = ''
fp = ''
track_id = ''


def wait_for_start(buy_time):
    submit_time = datetime.datetime.strptime(buy_time, '%Y-%m-%d %H:%M:%S.%f') + datetime.timedelta(seconds=-0.15)
    submit_time_ms = int(time.mktime(submit_time.timetuple()) * 1000.0 + submit_time.microsecond / 1000)
    jd_time = get_jd_time()
    diff_time = jd_time - int(time.time() * 1000)
    logger.info('正在等待到达设定时间【{}】，检测时间误差为【{}】毫秒'.format(buy_time, diff_time))
    while True:
        if int(time.time() * 1000) + diff_time > submit_time_ms:
            logger.info('时间到达，开始执行……')
            break
        else:
            time.sleep(0.001)


def get_jd_time():
    url = 'https://api.m.jd.com/client.action?functionId=queryMaterialProducts&client=wh5'
    try:
        resp = requests.get(url=url, headers=headers, timeout=2)
        resp_json = json.loads(resp.text)
        jd_time = resp_json.get('currentTime2')
        return int(jd_time)
    except Exception:
        return int(time.time() * 1000)


def get_buy_time(sku_id):
    url = 'https://item-soa.jd.com/getWareBusiness?skuId={}'.format(sku_id)
    try:
        resp = requests.get(url=url, headers=headers)
        data = re.findall('"buyTime":"(.*)","cdPrefix"', resp.text)
        if data and data[0]:
            buy_time = data[0][0:16] + ':00.00'
            logger.info('商品【{}】抢购时间【{}】'.format(sku_id, buy_time))
            return buy_time
    except Exception as e:
        logger.error('获取商品抢购时间异常：{}'.format(e))


def get_item_title(sku_id):
    url = 'https://item.jd.com/{}.html'.format(sku_id)
    try:
        resp = requests.get(url=url, headers=headers)
        title = re.findall('<title>(.*?)</title>', resp.text)[0][:-16]
        return title
    except Exception as e:
        logger.error('获取商品标题异常：{}'.format(e))


def get_item_price(sku_id):
    url = 'https://p.3.cn/prices/mgets?skuIds=J_{}'.format(sku_id)
    try:
        resp = requests.get(url=url)
        resp_json = parse_json(resp.text)
        return resp_json.get('p')
    except Exception as e:
        logger.error('获取商品价格异常：{}'.format(e))


def get_reserve_url(sku_id):
    url = 'https://yushou.jd.com/youshouinfo.action?sku={}'.format(sku_id)
    try:
        resp = requests.get(url=url, headers=headers)
        resp_json = json.loads(resp.text)
        reserve_url = resp_json.get('url')
        if reserve_url:
            return 'https:' + reserve_url
    except Exception as e:
        logger.error('获取预约链接异常：{}'.format(e))


def make_reserve(session, sku_id):
    reserve_url = get_reserve_url(sku_id)
    if not reserve_url:
        logger.info('非预约商品【{}】'.format(sku_id))
        return
    try:
        resp = session.get(url=reserve_url)
        soup = BeautifulSoup(resp.text, 'html.parser')
        result = soup.find('p', {'class': 'bd-right-result'}).text.strip(' \t\r\n')
        title = get_item_title(sku_id)
        logger.info('【{}】【{}】'.format(title, result))
    except Exception as e:
        logger.error('商品预约异常：{}'.format(e))


def clear_cart(session):
    select_url = 'https://cart.jd.com/selectAllItem.action'
    remove_url = 'https://cart.jd.com/batchRemoveSkusFromCart.action'
    try:
        select_resp = session.post(url=select_url)
        remove_resp = session.post(url=remove_url)
        if select_resp.status_code == requests.codes.OK and remove_resp.status_code == requests.codes.OK:
            logger.info('清空购物车成功')
            return True
        else:
            logger.info('清空购物车失败')
            return False
    except Exception as e:
        logger.error('清空购物车异常：{}'.format(e))
        return False


def add_item_to_cart(session, sku_id, num):
    url = 'https://cart.jd.com/gate.action'
    payload = {
        'pid': sku_id,
        'pcount': num,
        'ptype': 1,
    }
    try:
        resp = session.get(url=url, params=payload)
        if '加购成功' in resp.text:
            logger.info('【{}:{}】加入购物车成功'.format(sku_id, num))
            return True
        else:
            logger.info('【{}:{}】加入购物车失败'.format(sku_id, num))
            return False
    except Exception as e:
        logger.error('加入购物车异常：{}'.format(e))
        return False


def change_item_to_cart(session, sku_id, num):
    url = 'https://cart.jd.com/changeNum.action'
    payload = {
        'pid': sku_id,
        'pcount': num,
        'ptype': 1,
    }
    try:
        resp = session.get(url=url, params=payload)
        resp_json = json.loads(resp.text)
        if resp_json.get('sortedWebCartResult', {}).get('success'):
            logger.info('修改购物车成功')
        else:
            logger.info('修改购物车失败')
    except Exception as e:
        logger.error('修改购物车异常：{}'.format(e))


def select_all_cart_item(session):
    url = 'https://cart.jd.com/selectAllItem.action'
    try:
        session.get(url=url)
    except Exception as e:
        logger.error('选中商品异常：{}'.format(e))


def cancel_all_cart_item(session):
    url = 'https://cart.jd.com/cancelAllItem.action'
    try:
        session.get(url=url)
    except Exception as e:
        logger.error('取消选中商品异常：{}'.format(e))


def get_cart_order_info(session):
    url = 'http://trade.jd.com/shopping/order/getOrderInfo.action'
    try:
        resp = session.get(url=url)
        mb_list = re.findall('class="mb"', resp.text)
        if not mb_list:
            order_info = {
                'address': re.findall('寄送至：(.*?)</span>', resp.text)[0],
                'receiver': re.findall('收货人：(.*?)</span>', resp.text)[0],
                'total_price': re.findall('id="sumPayPriceId">(.*?)</span>', resp.text)[0][1:],
            }
            logger.info('总价【{}】收货信息【{}{}】'.format(
                order_info.get('total_price'), order_info.get('receiver'), order_info.get('address')))
            return order_info
        else:
            logger.info('生成订单信息失败')
            return {}
    except Exception as e:
        logger.error('生成订单信息异常：{}'.format(e))
        return {}


def submit_cart_order(session, sku_ids, order_info):
    url = 'https://trade.jd.com/shopping/order/submitOrder.action'
    data = {
        'overseaPurchaseCookies': '',
        'vendorRemarks': '[]',
        'submitOrderParam.sopNotPutInvoice': 'false',
        'submitOrderParam.trackID': 'TestTrackId',
        'submitOrderParam.ignorePriceChange': '0',
        'submitOrderParam.btSupport': '0',
        'riskControl': '',
        'submitOrderParam.isBestCoupon': 1,
        'submitOrderParam.jxj': 1,
        'submitOrderParam.trackId': track_id,
        'submitOrderParam.eid': eid,
        'submitOrderParam.fp': fp,
        'submitOrderParam.needCheck': 1,
    }
    headers['Referer'] = 'http://trade.jd.com/shopping/order/getOrderInfo.action'
    try:
        resp = session.post(url=url, data=data, headers=headers)
        resp_json = json.loads(resp.text)
        order_id = resp_json.get('orderId')
        message = resp_json.get('message')
        result_code = resp_json.get('resultCode')
        if order_id:
            real_name = jd_account.get_user_info(session)
            msg = '账号【{}】下单成功【{}】订单号【{}】总价【{}】收货信息【{}{}】'.format(
                real_name, sku_ids, order_id, order_info.get('total_price'),
                order_info.get('receiver'), order_info.get('address'))
            logger.info(msg)
            save_msg(msg)
        else:
            logger.info('下单失败【{}】返回信息【{}】'.format(result_code, message))
        return order_id, result_code
    except Exception as e:
        logger.error('提交加购订单异常：{}'.format(e))
        return 0, 0


def cart_seckill_one(session, sku_ids, retry, interval):
    items_dict = parse_sku_id(sku_ids)
    for count in range(1, retry + 1):
        logger.info('第【{}/{}】次尝试抢购商品'.format(count, retry))
        for sku_id, num in items_dict.items():
            cancel_all_cart_item(session)
            change_item_to_cart(session, sku_id, num)
            order_info = get_cart_order_info(session)
            if not order_info:
                continue
            order_id, result_code = submit_cart_order(session, sku_id, order_info)
            if order_id:
                return True
            if result_code == 60040 or result_code == 60077:
                clear_cart(session)
                for sku_id, num in items_dict.items():
                    add_item_to_cart(session, sku_id, num)
            elif result_code == 60123:
                jd_account.not_use_jdbean(session)
                jd_account.not_use_red_packet(session)
            time.sleep(interval)
    logger.info('执行结束，抢购失败')


def cart_seckill_one_by_time(session, sku_ids, buy_time, retry=10, interval=2):
    clear_cart(session)
    items_dict = parse_sku_id(sku_ids)
    for sku_id, num in items_dict.items():
        make_reserve(session, sku_id)
        add_item_to_cart(session, sku_id, num)
    logger.info('准备抢购商品【{}】'.format(sku_ids))
    jd_account.not_use_jdbean(session)
    jd_account.not_use_red_packet(session)
    wait_for_start(buy_time)
    cart_seckill_one(session, sku_ids, retry, interval)


def cart_seckill(session, sku_id, num, retry, interval):
    clear_cart(session)
    if add_item_to_cart(session, sku_id, num):
        jd_account.not_use_jdbean(session)
        jd_account.not_use_red_packet(session)
        for count in range(1, retry + 1):
            logger.info('第【{}/{}】次尝试抢购商品'.format(count, retry))
            select_all_cart_item(session)
            order_info = get_cart_order_info(session)
            if not order_info:
                continue
            order_id, result_code = submit_cart_order(session, sku_id, order_info)
            if order_id:
                return True
            if result_code == 60040:
                change_item_to_cart(session, sku_id, num)
            elif result_code == 60077:
                add_item_to_cart(session, sku_id, num)
            elif result_code == 60123:
                jd_account.not_use_jdbean(session)
                jd_account.not_use_red_packet(session)
            time.sleep(interval)
        logger.info('执行结束，抢购失败')
        return False


def get_presale_order_info(session, sku_id, num):
    url = 'https://cart.jd.com/cart/dynamic/gateForSubFlow.action'
    payload = {
        'wids': sku_id,
        'nums': num,
        'subType': 32,
    }
    try:
        resp = session.get(url=url, params=payload)
        order_info = {
            'address': re.findall('寄送至：(.*?)</span>', resp.text)[0],
            'receiver': re.findall('收货人：(.*?)</span>', resp.text)[0],
            'total_price': re.findall('<strong>(.*?)</strong>', resp.text)[1][1:],
        }
        logger.info('总价【{}】收货信息【{}{}】'.format(
            order_info.get('total_price'), order_info.get('receiver'), order_info.get('address')))
        return order_info
    except Exception as e:
        logger.error('生成订单信息异常：{}'.format(e))
        return {}


def submit_presale_order(session, sku_id, order_info):
    url = 'https://trade.jd.com/shopping/order/submitOrder.action'
    data = {
        'overseaPurchaseCookies': '',
        'vendorRemarks': '[]',
        'submitOrderParam.sopNotPutInvoice': 'false',
        'submitOrderParam.presalePayType': '2',
        'submitOrderParam.trackID': 'TestTrackId',
        'flowType': '15',
        'preSalePaymentTypeInOptional': '2',
        'submitOrderParam.ignorePriceChange': '0',
        'submitOrderParam.btSupport': '0',
        'submitOrderParam.payType4YuShou': '2',
        'riskControl': '',
        'submitOrderParam.trackId': track_id,
        'submitOrderParam.eid': eid,
        'submitOrderParam.fp': fp,
        'submitOrderParam.jxj': 1,
        'submitOrderParam.needCheck': 1,
    }
    headers['Referer'] = 'https://trade.jd.com/shopping/order/getPresalInfo.action'
    try:
        resp = session.post(url=url, data=data, headers=headers)
        resp_json = json.loads(resp.text)
        order_id = resp_json.get('orderId')
        message = resp_json.get('message')
        result_code = resp_json.get('resultCode')
        if order_id:
            real_name = jd_account.get_user_info(session)
            msg = '账号【{}】下单成功【{}】订单号【{}】总价【{}】收货信息【{}{}】'.format(
                real_name, sku_id, order_id, order_info.get('total_price'),
                order_info.get('receiver'), order_info.get('address'))
            logger.info(msg)
            save_msg(msg)
        else:
            logger.info('下单失败【{}】返回信息【{}】'.format(result_code, message))
        return order_id, result_code
    except Exception as e:
        logger.error('提交预售订单异常：{}'.format(e))
        return 0, 0


def presale_seckill(session, sku_id, num, retry, interval):
    for count in range(1, retry + 1):
        logger.info('第【{}/{}】次尝试抢购商品'.format(count, retry))
        order_info = get_presale_order_info(session, sku_id, num)
        if not order_info:
            continue
        order_id, result_code = submit_presale_order(session, sku_id, order_info)
        if order_id:
            return True
        if result_code == 60123:
            jd_account.not_use_jdbean(session)
            jd_account.not_use_red_packet(session)
        time.sleep(interval)
    logger.info('执行结束，抢购失败')
    return False


def presale_seckill_by_time(session, sku_id, num, buy_time, retry=10, interval=2):
    logger.info('准备抢购商品【{}:{}】'.format(sku_id, num))
    jd_account.not_use_jdbean(session)
    jd_account.not_use_red_packet(session)
    wait_for_start(buy_time)
    presale_seckill(session, sku_id, num, retry, interval)


def get_seckill_url(sku_id, retry):
    url = 'https://itemko.jd.com/itemShowBtn?skuId={}'.format(sku_id)
    for i in range(0, retry):
        try:
            resp = requests.get(url=url, timeout=timeout)
            resp_json = parse_json(resp.text)
            if resp_json.get('url'):
                router_url = 'https:' + resp_json.get('url')
                seckill_url = router_url.replace('divide', 'marathon').replace('user_routing', 'captcha.html')
                logger.info('获取抢购链接成功【{}】'.format(seckill_url))
                return seckill_url
            else:
                logger.info('获取抢购链接失败【{}】不是抢购商品或页面暂未刷新'.format(sku_id))
        except Exception as e:
            logger.error('获取抢购链接异常：{}'.format(e))


def request_seckill_url(session, sku_id, seckill_url):
    headers['Referer'] = 'https://item.jd.com/{}.html'.format(sku_id)
    try:
        session.get(url=seckill_url, headers=headers, allow_redirects=False)
    except Exception as e:
        logger.error('访问抢购链接异常：{}'.format(e))


def request_seckill_checkout_page(session, sku_id, num):
    url = 'https://marathon.jd.com/seckill/seckill.action'
    payload = {
        'skuId': sku_id,
        'num': num,
    }
    headers['Referer'] = 'https://item.jd.com/{}.html'.format(sku_id)
    try:
        session.get(url=url, params=payload, headers=headers, allow_redirects=False)
    except Exception as e:
        logger.error('访问抢购结算页面异常：{}'.format(e))


def get_seckill_order_info(session, sku_id, num):
    url = 'https://marathon.jd.com/seckillnew/orderService/pc/init.action'
    data = {
        'sku': sku_id,
        'num': num,
    }
    try:
        resp = session.post(url=url, data=data, headers=headers)
        resp_json = json.loads(resp.text)
        if resp_json:
            address_info = resp_json.get('address', {})
            invoice_info = resp_json.get('invoiceInfo', {})
            order_info = {
                'skuId': sku_id,
                'num': num,
                'addressId': address_info.get('id'),
                'name': address_info.get('name'),
                'provinceId': address_info.get('provinceId'),
                'provinceName': address_info.get('provinceName'),
                'cityId': address_info.get('cityId'),
                'cityName': address_info.get('cityName'),
                'countyId': address_info.get('countyId'),
                'countyName': address_info.get('countyName'),
                'townId': address_info.get('townId'),
                'townName': address_info.get('townName'),
                'addressDetail': address_info.get('addressDetail'),
                'mobile': address_info.get('mobile'),
                'mobileKey': address_info.get('mobileKey'),
                'email': address_info.get('email'),
                'invoiceTitle': invoice_info.get('invoiceTitle'),
                'invoiceContent': invoice_info.get('invoiceContentType'),
                'invoicePhone': invoice_info.get('invoicePhone'),
                'invoicePhoneKey': invoice_info.get('invoicePhoneKey'),
                'invoice': 'true' if invoice_info else 'false',
                'overseas': address_info.get('overseas'),
                'phone': address_info.get('phone'),
                'token': resp_json.get('token'),
            }
            logger.info('总价【{}】收货信息【{}{}{}{}{}{}{}】'.format(
                resp_json.get('orderPriceBO', {}).get('totalPrice'), order_info.get('name'), order_info.get('mobile'),
                order_info.get('provinceName'), order_info.get('cityName'), order_info.get('countyName'),
                order_info.get('townName'), order_info.get('addressDetail')))
            return order_info
        else:
            return {}
    except Exception as e:
        logger.error('生成订单信息异常：{}'.format(e))
        return {}


def submit_seckill_order(session, sku_id, num, order_info):
    url = 'https://marathon.jd.com/seckillnew/orderService/pc/submitOrder.action?skuId={}'.format(sku_id)
    headers['Referer'] = 'https://marathon.jd.com/seckill/seckill.action?skuId={}&num={}'.format(sku_id, num)
    if order_info:
        order_info['pru'] = ''
        order_info['codTimeType'] = 3
        order_info['paymentType'] = 4
    try:
        resp = session.post(url=url, data=order_info, headers=headers, timeout=timeout)
        resp_json = json.loads(resp.text)
        if resp_json.get('success'):
            order_id = resp_json.get('orderId')
            total_money = resp_json.get('totalMoney')
            real_name = jd_account.get_user_info(session)
            msg = '账号【{}】抢购成功【{}】订单号【{}】总价【{}】收货信息【{}{}】'.format(
                real_name, sku_id, order_id, total_money, order_info.get('name'), order_info.get('addressDetail'))
            logger.info(msg)
            save_msg(msg)
            return True
        else:
            logger.info('抢购失败【{}】返回信息【{}】'.format(resp_json.get('resultCode'), resp_json.get('errorMessage')))
            return False
    except Exception as e:
        logger.error('提交抢购订单异常：{}'.format(e))
        return False


def exec_seckill(session, sku_id, num, retry, interval):
    order_info = {}
    seckill_url = get_seckill_url(sku_id, retry * 2)
    if seckill_url:
        request_seckill_url(session, sku_id, seckill_url)
        request_seckill_checkout_page(session, sku_id, num)
        for count in range(1, retry + 1):
            logger.info('第【{}/{}】次尝试抢购商品'.format(count, retry))
            if not order_info:
                order_info = get_seckill_order_info(session, sku_id, num)
            if submit_seckill_order(session, sku_id, num, order_info):
                return True
            time.sleep(interval)
    logger.info('执行结束，抢购失败')
    return False


def exec_seckill_by_time(session, sku_id, num, buy_time, retry=10, interval=0.1):
    logger.info('准备抢购商品【{}:{}】'.format(sku_id, num))
    jd_account.not_use_jdbean(session)
    jd_account.not_use_red_packet(session)
    wait_for_start(buy_time)
    exec_seckill(session, sku_id, num, retry, interval)


def get_item_stock(sku_id_list, area_id):
    start = int(time.time() * 1000)
    url = 'https://cd.jd.com/stocks'
    payload = {
        'skuIds': ','.join(sku_id_list),
        'area': area_id,
        'type': 'getstocks',
    }
    stock_list = []
    try:
        resp = requests.get(url=url, params=payload, headers=headers, timeout=timeout)
        resp_json = json.loads(resp.text)
        for sku_id, info in resp_json.items():
            sku_state = info.get('skuState')
            stock_state = info.get('StockState')
            if sku_state == 1 and stock_state in (33, 36, 40):
                stock_list.append(sku_id)
        logger.info('检测【{}】个商品有货，用时【{}】毫秒'.format(len(stock_list), int(time.time() * 1000) - start))
        return stock_list
    except requests.exceptions.Timeout:
        logger.error('查询【{}】库存信息超时'.format(sku_id_list))
        return stock_list
    except Exception as e:
        logger.error('查询库存信息异常：{}'.format(e))
        return stock_list


def buy_item_in_stock(session_list, sku_ids, area_id, retry=2, interval=2):
    items_dict = parse_sku_id(sku_ids)
    sku_id_list = list(items_dict.keys())
    while True:
        stock_list = get_item_stock(sku_id_list, area_id)
        for sku_id, num in items_dict.items():
            if sku_id in stock_list:
                logger.info('【{}】满足下单条件，开始执行'.format(sku_id))
                for session in session_list:
                    threading.Thread(target=cart_seckill, args=(session, sku_id, num, retry, interval)).start()
                    threading.Thread(target=presale_seckill, args=(session, sku_id, num, retry, interval)).start()
                    threading.Thread(target=exec_seckill, args=(session, sku_id, num, retry, interval)).start()
        time.sleep(interval)


def get_order_list(session):
    url = 'https://order.jd.com/center/list.action'
    try:
        resp = session.get(url=url, headers=headers)
        soup = BeautifulSoup(resp.text, 'html.parser')
        order_table = soup.find('table', {'class': 'order-tb'})
        table_bodies = order_table.select('tbody')
        exist_order = False
        for table_body in table_bodies:
            order_status = get_tag_value(table_body.select('span.order-status'))
            wait_payment = '等待付款' in order_status
            exist_order = True
            tr_th = table_body.select('tr.tr-th')[0]
            order_time = get_tag_value(tr_th.select('span.dealtime'))
            order_id = get_tag_value(tr_th.select('span.number a'))
            sum_price = ''
            pay_method = ''
            amount_div = table_body.find('div', {'class': 'amount'})
            if amount_div:
                spans = amount_div.select('span')
                pay_method = get_tag_value(spans, index=1)
                if wait_payment:
                    sum_price = get_tag_value(amount_div.select('strong'), index=1)[1:]
                else:
                    sum_price = get_tag_value(spans, index=0)[1:]
            name = ''
            address = ''
            receiver_div = table_body.find('div', {'class': 'pc'})
            if receiver_div:
                name = get_tag_value(receiver_div.select('strong'))
                address = get_tag_value(receiver_div.select('p'))
            items_dict = dict()
            tr_bds = table_body.select('tr.tr-bd')
            for tr_bd in tr_bds:
                item = tr_bd.find('div', {'class': 'goods-item'})
                if not item:
                    break
                item_id = item.get('class')[1][2:]
                quantity = get_tag_value(tr_bd.select('div.goods-number'))[1:]
                items_dict[item_id] = quantity
            logger.info('下单时间【{}】订单号【{}】商品列表【{}】订单状态【{}】总金额【{}】付款方式【{}】收货信息【{} {}】'.format(
                order_time, order_id, parse_items_dict(items_dict), order_status, sum_price, pay_method, name, address))
        if not exist_order:
            logger.info('查询订单信息为空')
    except Exception as e:
        logger.error('查询订单信息异常：{}'.format(e))
