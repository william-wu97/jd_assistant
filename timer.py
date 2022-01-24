# coding=UTF-8
import json
import time
import datetime
import requests
from log import logger


class Timer(object):

    def __init__(self, buy_time, sleep_interval=0.01):
        self.buy_time = datetime.datetime.strptime(buy_time, '%Y-%m-%d %H:%M:%S.%f')
        self.submit_time = self.buy_time + datetime.timedelta(seconds=-0.15)
        self.submit_time_ms = int(
            time.mktime(self.submit_time.timetuple()) * 1000.0 + self.submit_time.microsecond / 1000)
        self.sleep_interval = sleep_interval
        self.diff_time = self.local_jd_time_diff()

    def jd_time(self):
        url = 'https://api.m.jd.com/client.action?functionId=queryMaterialProducts&client=wh5'
        try:
            resp = requests.get(url)
            resp_json = json.loads(resp.text)
            return int(resp_json['currentTime2'])
        except Exception as e:
            logger.error(e)

    def local_time(self):
        return int(time.time() * 1000)

    def local_jd_time_diff(self):
        local_time1 = self.local_time()
        jd_time = self.jd_time()
        local_time2 = self.local_time()
        if jd_time:
            return jd_time - local_time1
        else:
            return local_time2 - local_time1

    def start(self):
        logger.info('正在等待到达设定时间【%s】，检测时间误差为【%s】毫秒', self.buy_time, self.diff_time)
        while True:
            if self.local_time() + self.diff_time >= self.submit_time_ms:
                logger.info('时间到达，开始执行……')
                break
            else:
                time.sleep(self.sleep_interval)
