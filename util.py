# coding=UTF-8
import os
import json
import configparser


def init_config(file_name='config.ini'):
    file = os.path.join(os.getcwd(), file_name)
    config = configparser.RawConfigParser()
    if not os.path.exists(file):
        config.add_section('config')
        config.add_section('account')
        config.set('account', 'cookies', 'value')
        with open(file_name, 'w') as f:
            config.write(f)
    config.read(file, encoding='utf-8-sig')
    sections = config.sections()
    if 'config' not in sections:
        config.add_section('config')
        with open(file_name, 'w') as f:
            config.write(f)
    if 'account' not in sections:
        config.add_section('account')
        config.set('account', 'cookies', 'value')
        with open(file_name, 'w') as f:
            config.write(f)


def get_config(file_name='config.ini'):
    file = os.path.join(os.getcwd(), file_name)
    config = configparser.RawConfigParser()
    config.read(file, encoding='utf-8-sig')
    return config.items('config')


def save_image(resp, image_file):
    with open(image_file, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=1024):
            f.write(chunk)


def open_image(image_file):
    if os.name == 'nt':
        os.system('start ' + image_file)
    else:
        if os.uname()[0] == 'Linux':
            if 'deepin' in os.uname()[2]:
                os.system('deepin-image-viewer ' + image_file)
            else:
                os.system('eog ' + image_file)
        else:
            os.system('open ' + image_file)


def get_tag_value(tag, key='', index=0):
    if key:
        value = tag[index].get(key)
    else:
        value = tag[index].text
    return value.strip(' \t\r\n')


def list_to_json(item_list):
    json = {}
    for item in item_list:
        json[item[0]] = item[1]
    return json


def parse_items_dict(dt):
    result = ''
    for index, key in enumerate(dt):
        if index < len(dt) - 1:
            result = result + '{0}:{1}, '.format(key, dt[key])
        else:
            result = result + '{0}:{1}'.format(key, dt[key])
    return result


def parse_json(js):
    begin = js.find('{')
    end = js.rfind('}') + 1
    return json.loads(js[begin:end])


def parse_sku_id(sku_ids):
    if isinstance(sku_ids, dict):
        return sku_ids
    item_list = list(filter(bool, map(lambda x: x.strip(), sku_ids.split(','))))
    result = dict()
    for item in item_list:
        if ':' in item:
            sku_id, num = map(lambda x: x.strip(), item.split(':'))
            result[sku_id] = num
        else:
            result[item] = '1'
    return result


def save_msg(string, file_name='result.ini'):
    file = os.path.join(os.getcwd(), file_name)
    config = configparser.RawConfigParser()
    if not os.path.exists(file):
        config.add_section('result')
        with open(file_name, 'w') as f:
            config.write(f)
    config.read(file, encoding='utf-8-sig')
    sections = config.sections()
    if 'result' not in sections:
        config.add_section('result')
    options = config.options('result')
    config.set('result', 'msg' + str(len(options) + 1), string)
    with open(file_name, 'w') as f:
        config.write(f)
