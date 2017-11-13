# -*- coding: utf-8 -*-
import scrapy
import logging
from scrapy.utils.response import get_base_url, open_in_browser
from bs4 import BeautifulSoup
from utils.text_util import remove_multi_space, remove_newline_character
from items import HexunItem
import traceback
import json


logger = logging.getLogger(__name__)

# 爬取首页 (http://www.hexun.com) 左上 新闻链接内部的页面
class EastMoneyOneStock(scrapy.Spider):
    name = 'eastmoney_onestock'
    allowed_domains = ['eastmoney.com']
    start_urls = ['http://quote.eastmoney.com']

    def parse(self, response):
        pass

    def parse_one_stock(self, stock_id):
        pass

