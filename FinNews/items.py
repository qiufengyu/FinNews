# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class WallStreetItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title = scrapy.Field()
    summary = scrapy.Field()
    source = scrapy.Field()
    url = scrapy.Field()
    pb_time = scrapy.Field()
    # author 在这里不明确，source 指向即可
    para_content_text_and_images = scrapy.Field()

class HexunItem(scrapy.Item):
    url = scrapy.Field()
    cur_source = scrapy.Field()
    title = scrapy.Field()
    pb_time = scrapy.Field()
    source = scrapy.Field()
    author = scrapy.Field()
    para_content_text_and_images = scrapy.Field()


class EastMoneyStockIdNameItem(scrapy.Item):
    stock_market = scrapy.Field()
    stock_name = scrapy.Field()
    stock_id = scrapy.Field()

class EastMoneyStockMapUserItem(scrapy.Item):
    stock_id = scrapy.Field()
    userid_list = scrapy.Field()

class EastMoneyStockUserInfoItem(scrapy.Item):
    userid = scrapy.Field()
    name = scrapy.Field()
    sex = scrapy.Field()
    edu = scrapy.Field()
    age = scrapy.Field()
    duty = scrapy.Field()
    start_time = scrapy.Field()
    intro = scrapy.Field()
    stock_id = scrapy.Field()

