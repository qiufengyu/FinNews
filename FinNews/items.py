# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class UserItem(scrapy.Item):
    username = scrapy.Field()
    password = scrapy.Field()
    email = scrapy.Field()
    recent_reads_url = scrapy.Field()
    recent_reads_title = scrapy.Field()
    tags = scrapy.Field()
    stocks = scrapy.Field()

class WallStreetItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    title = scrapy.Field()
    summary = scrapy.Field()
    source = scrapy.Field()
    url = scrapy.Field()
    pb_time = scrapy.Field()
    reads = scrapy.Field()
    # author 在这里不明确，source 指向即可
    para_content_text_and_images = scrapy.Field()

class HexunItem(scrapy.Item):
    url = scrapy.Field()
    cur_source = scrapy.Field()
    title = scrapy.Field()
    pb_time = scrapy.Field()
    source = scrapy.Field()
    author = scrapy.Field()
    reads = scrapy.Field()
    para_content_text_and_images = scrapy.Field()

class SinaItem(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    pb_time = scrapy.Field()
    source = scrapy.Field()
    author = scrapy.Field()
    reads = scrapy.Field()
    para_content_text_and_images = scrapy.Field()

class SinaRollItem(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    pb_time = scrapy.Field()
    source = scrapy.Field()
    author = scrapy.Field()
    reads = scrapy.Field()
    para_content_text_and_images = scrapy.Field()
    category = scrapy.Field()

class TencentItem(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    pb_time = scrapy.Field()
    source = scrapy.Field()
    author = scrapy.Field()
    reads = scrapy.Field()
    para_content_text_and_images = scrapy.Field()
    category = scrapy.Field()

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

# 各种公告
class EastMoneyAnnounceItem(scrapy.Item):
    url = scrapy.Field()
    title = scrapy.Field()
    type = scrapy.Field()
    anno_time = scrapy.Field()
    source_pdf_url = scrapy.Field()
    content = scrapy.Field()


# 各种新闻
class EastMoneyArticleItem(scrapy.Item):
    url = scrapy.Field()
    cur_source = scrapy.Field()
    title = scrapy.Field()
    type = scrapy.Field()
    pb_time = scrapy.Field()
    source = scrapy.Field()
    author = scrapy.Field()
    editor = scrapy.Field()
    comment_list = scrapy.Field()
    reads = scrapy.Field()
    para_content_text_and_images = scrapy.Field()


# 个股研报 - 行业研报
class EastMoneyResearchReportItem(scrapy.Item):
    url = scrapy.Field()
    research_report_type = scrapy.Field()
    title = scrapy.Field()
    pb_time = scrapy.Field()
    ping_ji = scrapy.Field()
    ji_gou = scrapy.Field()
    author = scrapy.Field()
    reads = scrapy.Field()
    img_k_url = scrapy.Field()
    img_k_alt = scrapy.Field()
    two_img_url = scrapy.Field()
    # img_price_tips = Field()
    para_content_text_and_images = scrapy.Field()