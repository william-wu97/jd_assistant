# coding=UTF-8
import os
import sys
import json
import time
import random
import requests
import configparser
from log import logger
from util import parse_json, save_image, open_image

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'}


def load_cookies(file_name='config.ini'):
    file = os.path.join(os.getcwd(), file_name)
    config = configparser.RawConfigParser()
    config.read(file, encoding='utf-8-sig')
    string = config.get('account', 'cookies')
    cookies = string_to_cookies(string)
    if cookies:
        session = requests.session()
        session.headers = headers
        session.cookies = cookies
        if check_login(session):
            return True
    return False


def get_account(file_name='config.ini'):
    file = os.path.join(os.getcwd(), file_name)
    config = configparser.RawConfigParser()
    config.read(file, encoding='utf-8-sig')
    return config.items('account')


def save_cookies(cookies, file_name='config.ini'):
    string = cookies_to_string(cookies)
    file = os.path.join(os.getcwd(), file_name)
    config = configparser.RawConfigParser()
    config.read(file, encoding='utf-8-sig')
    config.set('account', 'cookies', string)
    with open(file_name, 'w') as f:
        config.write(f)


def string_to_cookies(string):
    try:
        item_list = string.split(';')
        cookies_dict = {}
        for item in item_list:
            if item:
                name, value = item.strip().split('=', 1)
                cookies_dict[name] = value
        cookies = requests.utils.cookiejar_from_dict(cookies_dict, cookiejar=None, overwrite=True)
        return cookies
    except Exception as e:
        logger.error('cookies转换异常：{}'.format(e))


def cookies_to_string(cookies):
    try:
        cookies_dict = requests.utils.dict_from_cookiejar(cookies)
        string = ''
        for item in cookies_dict:
            string += item + '=' + cookies_dict[item] + ';'
        return string[:-1]
    except Exception as e:
        logger.error('cookies转换异常：{}'.format(e))


def get_qr_code(session):
    url = 'https://qr.m.jd.com/show'
    payload = {
        'appid': 133,
        'size': 147,
    }
    try:
        resp = session.get(url=url, params=payload, headers=headers)
        if resp.status_code != requests.codes.OK:
            return False
        qr_code_file = 'qr_code.png'
        save_image(resp, qr_code_file)
        logger.info('获取二维码成功，请打开京东APP扫描')
        open_image(qr_code_file)
        return True
    except Exception as e:
        logger.error('获取二维码异常：{}'.format(e))


def get_qr_code_ticket(session):
    url = 'https://qr.m.jd.com/check'
    payload = {
        'appid': '133',
        'callback': 'jQuery{}'.format(random.randint(1000000, 9999999)),
        'token': session.cookies.get('wlfstk_smdl'),
    }
    headers['Referer'] = 'https://plogin.m.jd.com/login/login'
    try:
        resp = session.get(url=url, params=payload, headers=headers)
        if resp.status_code != requests.codes.OK:
            logger.info('获取二维码扫描结果失败')
            return ''
        resp_json = parse_json(resp.text)
        logger.info(resp_json)
        if resp_json.get('code') == 200:
            logger.info('已完成手机客户端确认')
            return resp_json.get('ticket')
    except Exception as e:
        logger.error('获取二维码扫描结果异常：{}'.format(e))


def check_qr_code_ticket(session, ticket):
    url = 'https://passport.jd.com/uc/qrCodeTicketValidation?t={}'.format(ticket)
    headers['Referer'] = 'https://passport.jd.com/uc/login?ltype=logout'
    try:
        resp = session.get(url=url, headers=headers)
        if resp.status_code != requests.codes.OK:
            return False
        resp_json = json.loads(resp.text)
        if resp_json.get('returnCode') == 0:
            return True
        else:
            return False
    except Exception as e:
        logger.error('校验二维码信息异常：{}'.format(e))


def get_user_info(session):
    url = 'https://passport.jd.com/user/petName/getUserInfoForMiniJd.action'
    headers['Referer'] = 'https://order.jd.com/center/list.action'
    try:
        resp = session.get(url=url, headers=headers)
        resp_json = json.loads(resp.text)
        return resp_json.get('nickName')
    except Exception:
        return 'jd'


def check_login(session):
    url = 'https://order.jd.com/center/list.action'
    try:
        resp = session.get(url=url, allow_redirects=False)
        if resp.status_code == requests.codes.OK:
            nick_name = get_user_info(session)
            logger.info('登录成功用户【{}】'.format(nick_name))
            return True
        else:
            logger.info('校验登录失败')
            return False
    except Exception as e:
        logger.error('cookies校验异常：{}'.format(e))


def login_by_qr_code():
    session = requests.session()
    if not get_qr_code(session):
        logger.info('获取二维码失败')
        sys.exit()
    for i in range(0, 80):
        ticket = get_qr_code_ticket(session)
        if ticket:
            break
        time.sleep(2)
    else:
        logger.info('二维码过期，请重新获取扫描')
        sys.exit()
    if not check_qr_code_ticket(session, ticket):
        logger.info('校验二维码信息失败')
        sys.exit()
    if check_login(session):
        save_cookies(session.cookies)


def get_address_list(session):
    url = 'https://marathon.jd.com/seckillnew/addrService/pc/getAddressList.action'
    try:
        resp = session.post(url=url, headers=headers)
        resp_json = json.loads(resp.text)
        address_list = []
        for item in resp_json:
            area_id = '{}_{}_{}_{}'.format(
                item.get('provinceId'), item.get('cityId'), item.get('countyId'), item.get('townId'))
            address = {
                'id': item.get('id'),
                'area_id': area_id,
                'name': item.get('name'),
                'mobile': item.get('mobile'),
                'province_id': item.get('provinceId'),
                'city_id': item.get('cityId'),
                'county_id': item.get('countyId'),
                'town_id': item.get('townId'),
                'province_name': item.get('provinceName'),
                'city_name': item.get('cityName'),
                'county_name': item.get('countyName'),
                'town_name': item.get('townName'),
                'address_detail': item.get('addressDetail'),
                'default_address': item.get('defaultAddress'),
            }
            address_list.append(address)
        return address_list
    except Exception as e:
        logger.error('获取地址信息异常：{}'.format(e))
        return []


def get_address_id(area, address_list):
    result = address_list[0]
    if area:
        if area[0].isdigit():
            for address in address_list:
                if address['area_id'] == area:
                    result = address
        else:
            for address in address_list:
                if address['province_name'] == area:
                    result = address
    else:
        for address in address_list:
            if address['default_address']:
                result = address
    logger.info('地址信息【{}】【{}】【{}】【{}】【{}】【{}】'.format(
        result['id'], result['area_id'], result['name'], result['province_name'],
        result['address_detail'], result['default_address']))
    return result['id']


def set_cart_address(session, address_id):
    url = 'https://trade.jd.com/shopping/dynamic/consignee/saveConsignee.action'
    data = {
        'consigneeParam.newId': address_id
    }
    headers['Referer'] = 'https://trade.jd.com/shopping/order/getOrderInfo.action'
    try:
        resp = session.post(url=url, data=data, headers=headers)
    except Exception as e:
        logger.error('更新购物车地址异常：{}'.format(e))


def set_seckill_address(session, address_id):
    url = 'https://marathon.jd.com/seckillnew/addrService/pc/selectAddress.action'
    data = {
        'addressId': address_id
    }
    try:
        resp = session.post(url=url, data=data, headers=headers)
    except Exception as e:
        logger.error('更新抢购地址异常：{}'.format(e))


def set_address(session, area):
    address_list = get_address_list(session)
    address_id = get_address_id(area, address_list)
    set_cart_address(session, address_id)
    set_seckill_address(session, address_id)


def not_use_jdbean(session):
    url1 = 'https://trade.jd.com/shopping/dynamic/jdbean/useJdBean.action'
    url2 = 'https://marathon.jd.com/seckillnew/jBeanService/pc/useJBean.action'
    data1 = {
        'jdBeanParam.usedJdBean': 0
    }
    data2 = {
        'useCount': 0
    }
    try:
        session.post(url=url1, data=data1, headers=headers)
        session.post(url=url2, data=data2, headers=headers)
    except Exception as e:
        logger.error(e)


def not_use_red_packet(session):
    url = 'https://trade.jd.com/virtual/v1/red-packet'
    data = {
        'flowType': 0,
        'overseaMerge': 0,
        'preSalePaymentTypeInOptional': 0,
        'use': False,
    }
    headers['Content-Type'] = 'application/json'
    try:
        session.put(url=url, data=json.dumps(data), headers=headers)
    except Exception as e:
        logger.error(e)
