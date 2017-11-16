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
  name = 'sina_roll'
  allowed_domains = ['sina.com.cn']
  # dummy
  start_urls = ['http://roll.finance.sina.com.cn/s/channel.php']

  def parse(self, response):
    settings = get_project_settings()
    req = urllib.request.Request(url=settings['SINA_ROLL_FINANCE_NEWS'])
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
      yield scrapy.Request(r['url'], callback=self.parse_category, meta={
        'title': r['title'], 'pb_time': rtstr
      })
      # print(r['title'], rtstr)
      # print(r['url'])

  def parse_category(self, response):
    soup = BeautifulSoup(response.body, 'html5lib')
    meta_info = {'url': response.url,
                 'title': response.meta['title'], 'pb_time': response.meta['pb_time'],
                }
    if soup.find('div', 'bread'):
      cursors = soup.find('div', 'bread').text.strip()
      # print(cursors)
      # Scrapy 默认不会爬取重复 url 的内容，这里我们再爬取一次，设置 dont_filter=True
      # 直接把函数搬过来，但是我觉得结构、逻辑上就不美观了
      """
      if '证券' in cursors:
        print('证券', response.url)
        yield scrapy.Request(response.url, callback=self.parse_common_contents, meta={
          'title': response.meta['title'], 'pb_time': response.meta['pb_time'], 'category': '证券'
        }, dont_filter=True)
      """
      # 为了提高爬虫效率，使用如下的代码

      if '证券' in cursors:
        # print('证券', response.url)
        meta_info['category'] = '证券'
      elif '港股' in cursors:
        meta_info['category'] = '港股'
      elif '国内财经' in cursors:
        meta_info['category'] = '国内财经'
      elif '国际财经' in cursors:
        meta_info['category'] = '国际财经'
      elif '期货' in cursors:
        meta_info['category'] = '期货'
      elif '产经' in cursors:
        meta_info['category'] = '产经'
      else:
        pass
      yield self.parse_common_contents(soup, meta_info=meta_info)
    elif soup.find('p', 'fl'):
      if '美股' in soup.find('p', 'fl').text:
        meta_info['category'] = '美股'
        yield self.parse_usstock_contents(soup, meta_info=meta_info)

  def parse_common_contents(self, soup, meta_info):
    # print(response.url)
    item = SinaRollItem()
    item['url'] = meta_info['url']
    item['category'] = meta_info['category']
    item['pb_time'] = meta_info['pb_time']
    page_info = soup.find('div', 'page-info')
    source = None
    if page_info:
      source = page_info.find('span').text
      source = remove_multi_space(source).strip()
    source = source.split(' ')[1]
    item['source'] = source
    para_content_text_and_images = []
    author = soup.find('p', 'article-editor').text.strip()
    author = author[author.index('：') + 1:]
    item['author'] = author
    title = soup.find('div', 'page-header')
    if title:
      title_text = remove_multi_space(title.text).strip()
    else:
      title_text = meta_info['title']
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

    return item

  def parse_usstock_contents(self, soup, meta_info):
    item = SinaRollItem()
    item['url'] = meta_info['url']
    item['title'] = meta_info['title']
    item['category'] = meta_info['category']
    item['pb_time'] = meta_info['pb_time']
    if soup.find('div', {'id': 'media_name'}):
      source = soup.find('div', {'id': 'media_name'}).text.strip()
    elif soup.find('span', {'id': 'media_name'}):
      source = soup.find('span', {'id': 'media_name'}).text.strip()
    source = source[:source.index('\xa0')]
    item['source'] = source
    content = soup.find('div', {'id': 'artibody'})
    para_content_text_and_images = []
    if content:
      paras = content.find_all(re.compile('^[pd]'))
      for para in list(paras):
        if para.find('img'):
          img_src = para.find('img')['src'].strip()
          if ('icon01' not in img_src) and ('usstocks' not in img_src):
            para_content_text_and_images.append(para.find('img')['src'].strip())
            descr = para.find('span', 'img_descr')
            if descr:
              descr_text = descr.text.strip()
              if len(descr_text) > 0:
                para_content_text_and_images.append(descr_text)
        else:
          para_content = remove_multi_space(remove_html_space(para.text).strip())
          # print(para_content)
          if len(para_content) > 0:
            para_content_text_and_images.append(para_content)
      author = content.find('p', 'article-editor').text.strip()
      author = author[author.index('：') + 1:]
    item['author'] = author
    item['para_content_text_and_images'] = para_content_text_and_images
    return item
