# jd_assistant

京东抢购助手（全新版本）

## 主要功能

- 登陆京东商城（[www.jd.com](http://www.jd.com/)）
  - 手机扫码登录
  - 保存/加载登录cookies（可验证cookies是否过期）
- 商品查询操作
  - 根据商品ID和地址ID查询库存
  - 根据商品ID查询价格
- 购物车操作
  - 清空/添加购物车（无货商品也可以加入购物车）
  - 获取购物车商品详情
- 订单操作
  - 获取订单结算页面信息（商品详情, 应付总额, 收货地址, 收货人等）
  - 提交订单（加购，预售，抢购）
    - 直接提交
    - 有货提交
    - 定时提交
  - 查询订单
- 其他
  - 商品预约
  - 获取抢购时间
  - 用户信息查询

## 运行环境

- [Python 3](https://www.python.org/)

## 第三方库

- [Requests](http://docs.python-requests.org/en/master/)
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)

## 使用教程

- 配置环境变量，路径为文件夹位置
- `main.py`为程序主入口，`config.ini`为配置文件
- `area_id`为库存监控的地区id
- `area`为下单地址的地区id，或者省份名称
- `sku_ids`为商品id，格式为商品id1:数量1,商品id2:数量2
- `buy_time`为抢购时间，会自动根据第一个商品id获取
- `mode`为模式选择，1.加购，2.预售，3.抢购，4.库存监控，5.查询订单
- 多个账号请在`config.ini`文件中按序填写
```
[account]
cookies=thor=xxxx
cookies1=thor=xxxx
```

## 注意事项

- 建议在京东订单结算页面设置发票为`电子普通发票-个人`，设置支付方式为`在线支付`，否则可能出现各种未知的下单失败问题。
- 建议在京东订单结算页面取消使用`红包`，`京豆`，或者提前下单任意商品使用，否则需要提供支付密码。
- 京东商城的登陆/下单机制经常改动，当前测试时间`2022.01.01`。如果失效，欢迎提issue。

## 待完成的功能

- [ ] 判断下单模式
- [ ] web交互界面

## 不考虑的功能

- ✖ 支付功能

## 支持
- 考研业余开发，欢迎合作支持。
- ![image](https://github.com/SSJACK8582/jd_assistant/blob/main/files/alipay.jpg)

## 感谢
[https://github.com/tychxn/jd-assistant]
