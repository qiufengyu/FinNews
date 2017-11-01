# -*- coding: utf-8 -*-
import scrapy
import logging
from scrapy.utils.response import get_base_url, open_in_browser
from bs4 import BeautifulSoup
from utils.text_util import remove_multi_space, remove_newline_character
from items import EastMoneyStockIdNameItem, EastMoneyStockMapUserItem, EastMoneyStockUserInfoItem
import traceback
import json


logger = logging.getLogger(__name__)


# 首先从 http://quote.eastmoney.com/stocklist.html#sz 爬取股票代码，然后分别爬取有趣的东西
class EastMoneySpider(scrapy.Spider):
    name = 'eastmoney'
    allowed_domains = ['eastmoney.com']

    url_map_parse = {
        'http://quote.eastmoney.com/stocklist.html': 'self.parse_stocklist',
    }
    start_urls = url_map_parse.keys()

    def parse(self, response):
        return eval(EastMoneySpider.url_map_parse[get_base_url(response)])(response)

    def parse_stocklist(self, response):
        soup = BeautifulSoup(response.body, "html5lib")
        for a_tag in soup.find('div', 'quotebody').findAll('a'):
            if 'href' not in a_tag.attrs:
                continue
            tx = a_tag.attrs['href']
            tx = tx[tx.rfind(u'/') + 1:tx.rfind('.html')]
            if len(tx) != 8:
                continue
            id_name = EastMoneyStockIdNameItem()
            txt = a_tag.get_text()
            id_name['stock_market'] = tx[:2]
            id_name['stock_name'] = txt[:txt.rfind(u'(')]
            id_name['stock_id'] = tx[2:]

            # 抓取公司股东的个人信息
            # req_url = 'http://emweb.securities.eastmoney.com/PC_HSF10/CompanyManagement/CompanyManagementAjax?code=' + tx
            # yield scrapy.Request(req_url, callback=self.parse_userinfo_json)

            if 'sh' in tx:
                # yield id_name
                print(id_name)
            if 'sz' in tx:
                # yield id_name
                print(id_name)
            yield id_name

    def parse_userinfo_json(self, response):
        stock_id = get_base_url(response)[-8:]
        userid_list = []
        json_data = json.loads(response.body, encoding='utf8')
        for one_man in json_data['Result']['RptManagerList']:
            name = one_man['xm']
            sex = one_man['xb']
            age = one_man['nl']
            edu = one_man['xl']
            duty = one_man['zw']
            start_time = one_man['rzsj']
            intro = one_man['jj']
            user_id = str(hash(name) % 100000) + str(hash(sex) % 10) + str(hash(age) % 100) + str(hash(edu) % 1000)

            yield EastMoneyStockUserInfoItem({'userid': user_id, 'name': name, 'sex': sex, 'edu': edu, 'age': age, \
                                              'duty': duty, 'start_time': start_time, 'intro': intro,
                                              'stock_id': stock_id, })
            userid_list.append(user_id)
        yield EastMoneyStockMapUserItem({'stock_id': stock_id, 'userid_list': userid_list})
