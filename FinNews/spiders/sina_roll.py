import re
import json
import urllib
import datetime

import scrapy

from bs4 import BeautifulSoup
from scrapy.utils.project import get_project_settings

from items import SinaRollItem
from utils.text_util import *

"""
使用浏览器浏览新浪财经滚动新闻，查看源代码发现有反爬虫机制
从 tushare 开源工具（https://github.com/waditu/tushare）中找到了 http 请求入口
根据上述方法获取最新滚动财经新闻
"""


class Dummy(dict):
  def __getitem__(self, item):
    return item


class SinaRollSpider(scrapy.Spider):
  settings = get_project_settings()
  name = 'sina_roll'
  allowed_domains = ['sina.com.cn']
  # dummy
  start_urls = ['http://roll.finance.sina.com.cn/s/channel.php']
  pages = settings['SINA_ROLL_PAGES']

  def parse(self, response):
    for i in range(1, self.pages+1):
      req = urllib.request.Request(url=self.settings['SINA_ROLL_FINANCE_NEWS'].format(i))
      response = urllib.request.urlopen(req, timeout=5)
      response_read = response.read().decode('gbk')
      data_str = response_read.split('=')[1][:-1]
      """
      解析非标准 JSON 的 Javascript 字符串
      """
      data_str = eval(data_str, Dummy())
      data_str = json.dumps(data_str)
      data_str = json.loads(data_str)
      data_str = data_str['list']
      for r in data_str:
        rt = datetime.datetime.fromtimestamp(r['time'])
        rtstr = datetime.datetime.strftime(rt, "%Y-%m-%d %H:%M")
        yield scrapy.Request(r['url'], callback=self.parse_common_contents, meta={
          'title': r['title'], 'pb_time': rtstr
        })
      # print(r['title'], rtstr)
      # print(r['url'])


  def parse_common_contents(self, response):
    soup = BeautifulSoup(response.body, 'lxml')
    # print(response.url)
    item = SinaRollItem()
    item['reads'] = 0
    item['url'] = response.url
    item['pb_time'] = response.meta['pb_time']

    if soup.find('div', 'channel-path'):
      cursors = soup.find('div', 'channel-path')
      category = cursors.find('a').text.strip()
    item['category'] = category if category else None

    page_info = soup.find('div', 'date-source')
    source = None
    if page_info and page_info.find('a', 'source'):
      source = page_info.find('a', 'source').text
      source = source.strip()
    elif page_info and page_info.find('span', 'source'):
      source = page_info.find('span', 'source').text
      source = source.strip()
    item['source'] = source
    para_content_text_and_images = []
    if soup.find('p', 'article-editor'):
      author = soup.find('p', 'article-editor').text.strip()
      author = author[author.index('：') + 1:]
    else:
      author = None
    item['author'] = author
    title = soup.find('div', 'main-title')
    if title:
      title_text = remove_multi_space(title.text).strip()
    else:
      title_text = response.meta['title']
    item['title'] = title_text
    # 正文
    artibody = soup.find('div', {'id': 'artibody'})
    paras = artibody.find_all(re.compile('^[pd]'))
    for para in list(paras):
      parent_node = para.parent.attrs
      if 'id' in parent_node.keys():
        if parent_node['id'] == 'artibody':
          # print(para.name, para.attrs)
          if para.find('img'):
            img_node = para.find('img')
            img = img_node['src'].strip()
            # 过滤广告，可能不太完美，存在一些问题
            if ('banner' not in img) and ('icon' not in img):
              if len(img) > 0:
                para_content_text_and_images.append(img)
          elif para.name == 'p':
            para_text = remove_multi_space(para.text).strip()
            if len(para_text) > 0:
              para_content_text_and_images.append(para_text)
    item['para_content_text_and_images'] = para_content_text_and_images
    yield item

