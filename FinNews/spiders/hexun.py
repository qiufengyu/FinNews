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
class HexunSpider(scrapy.Spider):
    name = 'hexun'
    allowed_domains = ['hexun.com']

    url_map_parse = {
                     'http://news.hexun.com': 'self.parse_news_hexun_com',
                     'http://news.hexun.com/original/': 'self.parse_news_hexun_com_original',
                     'http://news.hexun.com/domestic/': 'self.parse_news_hexun_com_domestic',
                     'http://news.hexun.com/events/': 'self.parse_news_hexun_com_events',
                     'http://news.hexun.com/company/': 'self.parse_news_hexun_com_company',
                     'http://news.hexun.com/listedcompany/': 'self.parse_news_hexun_com_listedcompany',
                     'http://news.hexun.com/international/': 'self.parse_news_hexun_com_international'
                     }
    start_urls = url_map_parse.keys()


    def parse(self, response):
        return eval(HexunSpider.url_map_parse[get_base_url(response)])(response)


    # http://news.hexun.com  和讯新闻
    def parse_news_hexun_com(self, response):
        soup = BeautifulSoup(response.body, "html5lib")
        # 提取 http://news.hexun.com 页面左侧的所有展示新闻
        for site in soup.find_all('div', 'l'):
            for li in site.find_all('li'):
                a_tag = li.find('a')
                if a_tag is not None:
                    if self.is_comparable(a_tag['href']):
                        yield scrapy.Request(a_tag['href'], callback=self.parse_article_contents)


    # http://news.hexun.com/original/  和讯独家, 和讯特稿
    def parse_news_hexun_com_original(self, response):
        req_url = 'http://open.tool.hexun.com/MongodbNewsService/data/getOriginalNewsList.jsp?id=100000000&s=300&cp=1&priority=0'
        yield scrapy.Request(req_url, callback=self.parse_original_json)


    # http://news.hexun.com/original/  财经要闻, 国内经济
    def parse_news_hexun_com_domestic(self, response):
        req_url = 'http://open.tool.hexun.com/MongodbNewsService/newsListPageByJson.jsp?id=100000000&s=300&cp=1&priority=0&callback=hx_json1150830672528'
        yield scrapy.Request(req_url, callback=self.parse_original_json)

    # http://news.hexun.com/events/  时事 时事要闻
    def parse_news_hexun_com_events(self, response):
        soup = BeautifulSoup(response.body, "html5lib")
        # 提取 http://news.hexun.com 页面左侧的所有展示新闻
        for site in soup.find_all('div', 'w620'):
            for li in site.find_all('li'):
                a_tag = li.find('a')
                if a_tag is not None:
                    if self.is_comparable(a_tag['href']):
                        yield scrapy.Request(a_tag['href'], callback=self.parse_article_contents)

    # http://news.hexun.com/company/ 产业 产业报道
    def parse_news_hexun_com_company(self, response):
        req_url = 'http://open.tool.hexun.com/MongodbNewsService/newsListPageByJson.jsp?id=100000000&s=300&cp=1&priority=0&callback=hx_json11508336428377'
        yield scrapy.Request(req_url, callback=self.parse_original_json)

    # http://news.hexun.com/listedcompany/ 公司 公司新闻
    def parse_news_hexun_com_listedcompany(self, response):
        req_url = 'http://open.tool.hexun.com/MongodbNewsService/newsListPageByJson.jsp?id=108511812&s=300&cp=1&priority=0&callback=hx_json11508337121500'
        yield scrapy.Request(req_url, callback=self.parse_original_json)

    # http://news.hexun.com/international/ 国际 国际经济
    def parse_news_hexun_com_international(self, response):
        req_url = 'http://open.tool.hexun.com/MongodbNewsService/newsListPageByJson.jsp?id=108511065&s=300&cp=1&priority=0&callback=hx_json11508337413727'
        yield scrapy.Request(req_url, callback=self.parse_original_json)

    def parse_original_json(self, response):
        try:
            json_data = json.loads(response.body, encoding='gbk')
        except ValueError as e:
            uu = str(response.body).decode('gbk')
            json_data = json.loads(uu[uu.find(u'{') : uu.rfind(u'}')+1], encoding='gbk')
        except Exception as e:
            print('exception url', response.url)
            traceback.print_exc()
            return
        for one in json_data['result']:
            if self.is_comparable(one['entityurl']):
                yield scrapy.Request(one['entityurl'], callback=self.parse_article_contents)

    def is_comparable(self, url):
        false_types = ['tv.hexun.com', 'guba.hexun.com', 'blog.hexun.com', 'tv.hexun.com', 'index.html']
        for one in false_types:
            if one in url:
                return False
        return True

    def parse_article_contents(self, response):
        url = get_base_url(response)
        soup = BeautifulSoup(response.body, "html5lib")

        #  start ---------------- cur_source [和讯网 收藏 鉴藏知识]
        cur_source = []
        try:
            for a_tag in soup.find('div', 'logonav clearfix').find('div', 'links').findAll('a'):
                cur_source.append(a_tag.get_text())
        except Exception as e:
            logger.warning('HexunSpider.parse_article_contents could not parsing: %s', url, exc_info=0)
            return

        # print ' '.join(cur_source)

        #  start ---------------- url, title, pb_time, source, author
        article_head = remove_multi_space(soup.find('div', 'layout mg articleName').get_text()).strip().split(' ')
        source = article_head[-1]
        index = -2
        while article_head[index].count(r':') != 2:
            source = article_head[index] + " " + source
            index -= 1
        author = ''
        if len(source.split(' ')) == 2:
            source, author = source.split(' ')

        pb_time = article_head[index - 1] + ' ' + article_head[index]
        title = ''.join(article_head[:index - 1])

        # print url, title, pb_time, source, author

        # start ---------------- para_content_text and images

        article_content = soup.find('div', 'art_context')
        all_content_text = remove_newline_character(remove_multi_space(article_content.get_text()).strip())
        str_article_content = remove_newline_character(remove_multi_space(str(article_content))).strip()
        para_content_text_and_images = []

        img_index = p_index = 0
        img_pro_index = p_pro_index = 0
        all_para = article_content.findAll('p')
        all_img = article_content.findAll('img')
        while True:
            # print 1, img_index, p_index
            img_index = str_article_content.find('<img', img_index)
            p_index = str_article_content.find('<p>', p_index)

            # print 2, img_index, p_index
            if img_index == -1 and p_index == -1:
                break

            if p_index == -1 or (img_index != -1 and img_index < p_index):
                im = all_img[img_pro_index]
                if 'alt' in im.attrs:
                    tt = remove_newline_character(remove_multi_space(im.attrs['alt']).strip())
                    para_content_text_and_images.append((tt, im.attrs['src']))
                img_pro_index += 1
                img_index += 20
            else:
                i, para = p_pro_index, all_para[p_pro_index]
                t_text = remove_newline_character(remove_multi_space(para.get_text()).strip())

                if i == 0:
                    j = all_content_text.find(t_text)
                    if j != -1:
                        para_content_text_and_images.append(all_content_text[:j])
                    para_content_text_and_images.append(t_text)
                elif i == len(all_para) - 1:
                    para_content_text_and_images.append(t_text)
                    j = all_content_text.find(t_text)
                    if j != -1:
                        para_content_text_and_images.append(all_content_text[j + len(t_text):])
                    tt = para_content_text_and_images[-1]
                    para_content_text_and_images[-1] = tt[:tt.find(u'看全文')].strip()
                else:
                    para_content_text_and_images.append(t_text)
                p_pro_index += 1
                p_index += 20

            # print 3, img_index, p_index
            pass

        # start ----------------- item construct
        article_item = HexunItem()
        article_item['url'] = url
        article_item['cur_source'] = cur_source
        article_item['title'] = title
        article_item['pb_time'] = pb_time
        article_item['source'] = source
        article_item['author'] = author
        article_item['para_content_text_and_images'] = para_content_text_and_images
        yield article_item

        pass
