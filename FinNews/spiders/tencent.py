import re
import sys
import time
import pprint
import platform

import scrapy

from bs4 import BeautifulSoup
from selenium import webdriver
from items import TencentItem
from utils.text_util import *


class TencentSpider(scrapy.Spider):
  name = 'tencent'
  start_urls = [
    'http://roll.finance.qq.com/'
  ]

  def config_driver(self):
    # set up chrome service
    if sys.platform.lower().startswith('win'):
      self.driver = webdriver.Chrome('../chromedriver')
    elif sys.platform.lower().startswith('darwin'):
      self.driver = webdriver.Chrome('chromedriver')
    else:
      print("Not supported platform")
      exit(-1)
    self.driver.set_page_load_timeout(1000)

  def parse(self, response):
    self.config_driver()
    self.driver.get(response.url)
    self.driver.maximize_window()
    time.sleep(5)  # Let the user actually see something!
    pages = 1
    while (pages <= 3):
      time.sleep(10)  # Let the user actually see something!
      source = self.driver.page_source

      soup = BeautifulSoup(source, 'lxml')
      article_container = soup.find('div', class_='list c')

      for news_item in article_container.find_all('li'):
        cate = news_item.find('span', 't-tit').text.strip()
        # pb_time = news_item.find('span', 't-time').text.strip()
        sub_url = news_item.find('a')['href']
        title = news_item.find('a').text.strip()
        # th['pb_time'] = pb_time
        yield scrapy.Request(sub_url, callback=self.parse_dir_contents, meta={
          'category': cate[1:-1], 'title': title})

      next_page = self.driver.find_elements_by_class_name('f12')
      next_page[-1].click()
      # all_handles = driver.window_handles
      # print(all_handles)
      # driver.switch_to_window(all_handles[-1])

      print("Page {} over".format(pages))
      pages += 1

  def __del__(self):
    self.driver.quit()
    print("Quit Chrome Driver")

  """
  带有重定向跳转的新闻比较麻烦
  包括 Gallery 类型的新闻，需要加载一定的时间
  如果再使用 selenium 是不是太复杂了？
  目前的处理方式不是很优雅
  """

  def parse_dir_contents_selenium(self, response):
    print("##$sselenium", response.url)
    item = TencentItem()
    title = response.meta['title']
    url = response.url
    category = response.meta['category']
    # extract here
    author = None
    pb_time = None
    ly = None
    para_content_text_and_images = []
    self.driver.get(response.url)
    time.sleep(10)
    # 强制刷新
    self.driver.maximize_window()
    self.driver.refresh()
    time.sleep(10)
    source = self.driver.page_source
    soup = BeautifulSoup(source, 'lxml')
    # 版式一
    # http://new.qq.com/cmsn/20171130021626 source time
    if soup.find('div', 'LEFT'):
      main_content = soup.find('div', 'LEFT')
      if main_content.find('h1'):
        title = main_content.find('h1').text.strip()
      if soup.find(attrs={'name': '_pbtime'}):
        pb_time = soup.find(attrs={'name': '_pbtime'})['content'].strip()
      if soup.find('div', 'LeftTool'):
        ly_flag = soup.find('div', 'LeftTool').find('span', {'data-bosszone': 'ly'})
        if ly_flag:
          ly = ly_flag.text.strip()
      # 似乎是为了兼容显示器的尺寸
      src_time = soup.find('div', 'a-src-time')
      if src_time:
        ss = src_time.find('a').text.strip()
        ss_split = ss.split()
        if len(ss_split) >= 2:
          ly = ss_split[0].strip()
          pb_time = "{} {}".format(ss_split[-2], ss_split[-1])
      contents = soup.find('div', 'content-article')
      if contents:
        paras = contents.find_all('p')
        for para in paras:
          if para.find('img'):
            para_content_text_and_images.append(para.find('img')['src'].strip())
          else:
            p_text = para.text.strip()
            if len(p_text) > 0:
              para_content_text_and_images.append(p_text)
    # Gallery 形式
    elif soup.find('div', 'gallery'):
      main_content = soup.find('div', 'qq_article')
      if main_content.find('div', 'hd'):
        title = main_content.find('div', 'hd').find('h1').text.strip()
      if main_content.find('div', 'a_Info'):
        a_info = main_content.find('div', 'a_Info')
        if a_info.find('span', 'a_source'):
          ly = a_info.find('span', 'a_source').text.strip()
        if a_info.find('span', 'a_time'):
          pb_time = a_info.find('span', 'a_time').text.strip()
        if a_info.find('span', 'a_author'):
          author = a_info.find('span', 'a_author').text.strip()
        if a_info.find('span', 'a_catelog'):
          category = a_info.find('span', 'a_catelog').text.strip()
      gallery = soup.find('div', 'gallery')
      pics = gallery.find('div', 'galleryList').find_all('li')
      for i in len(pics - 1):
        pic_url = url + "#p=" + str(i + 1)
        ga_pic = self.parse_gallery_picture(pic_url)
        if len(ga_pic) > 0:
          para_content_text_and_images.extend(ga_pic)
    # 版式二
    elif soup.find('div', 'qq_article'):
      main_content = soup.find('div', 'qq_article')
      if main_content.find('div', 'hd'):
        title = main_content.find('div', 'hd').find('h1').text.strip()
      if main_content.find('div', 'a_Info'):
        a_info = main_content.find('div', 'a_Info')
        if a_info.find('span', 'a_source'):
          ly = a_info.find('span', 'a_source').text.strip()
        if a_info.find('span', 'a_time'):
          pb_time = a_info.find('span', 'a_time').text.strip()
        if a_info.find('span', 'a_author'):
          author = a_info.find('span', 'a_author').text.strip()
        if a_info.find('span', 'a_catelog'):
          category = a_info.find('span', 'a_catelog').text.strip()
      contents = main_content.find('div', 'bd')
      if contents:
        paras = contents.find_all('p')
        for para in paras:
          if para.find('img'):
            para_content_text_and_images.append(para.find('img')['src'].strip())
          else:
            p_text = para.text.strip()
            if len(p_text) > 0:
              para_content_text_and_images.append(p_text)
        if len(paras) == 0:
          if contents.find('div', 'Cnt-Main-Article-QQ'):
            brs = contents.find('div', 'Cnt-Main-Article-QQ')
            for br in brs.find_all('br'):
              br.replace_with('\n')
            para_content_text_and_images.extend(contents.find('div', 'Cnt-Main-Article-QQ')
                                                .text.strip().split('\n'))
    else:
      print("=" * 20, " >>> Redirecting (selenium) or with other news format... <<< ", "=" * 20)
      yield None

    item['url'] = url
    item['title'] = title
    item['pb_time'] = pb_time
    item['source'] = ly
    item['category'] = category
    item['para_content_text_and_images'] = para_content_text_and_images
    item['author'] = author
    item['reads'] = 0

    yield item

  def parse_dir_contents(self, response):
    item = TencentItem()
    title = response.meta['title']
    url = response.url
    category = response.meta['category']
    # extract here
    author = None
    pb_time = None
    ly = None
    para_content_text_and_images = []
    soup = BeautifulSoup(response.body, 'lxml')
    # 版式一
    # http://new.qq.com/cmsn/20171130021626 source time
    if soup.find('div', 'LEFT'):
      main_content = soup.find('div', 'LEFT')
      if main_content.find('h1'):
        title = main_content.find('h1').text.strip()
      if soup.find(attrs={'name': '_pbtime'}):
        pb_time = soup.find(attrs={'name': '_pbtime'})['content'].strip()
      if soup.find('div', 'LeftTool'):
        ly_flag = soup.find('div', 'LeftTool').find('span', {'data-bosszone': 'ly'})
        if ly_flag:
          ly = ly_flag.text.strip()
      # 似乎是为了兼容显示器的尺寸
      src_time = soup.find('div', 'a-src-time')
      if src_time:
        ss = src_time.find('a').text.strip()
        ss_split = ss.split()
        if len(ss_split) >= 2:
          ly = ss_split[0].strip()
          pb_time = "{} {}".format(ss_split[-2], ss_split[-1])
      contents = soup.find('div', 'content-article')
      if contents:
        paras = contents.find_all('p')
        for para in paras:
          if para.find('img'):
            para_content_text_and_images.append(para.find('img')['src'].strip())
          else:
            p_text = para.text.strip()
            if len(p_text) > 0:
              para_content_text_and_images.append(p_text)
    # Gallery 形式
    elif soup.find('div', 'gallery'):
      yield self.parse_dir_contents_selenium(response)
    # 版式二
    elif soup.find('div', 'qq_article'):
      main_content = soup.find('div', 'qq_article')
      if main_content.find('div', 'hd'):
        title = main_content.find('div', 'hd').find('h1').text.strip()
      if main_content.find('div', 'a_Info'):
        a_info = main_content.find('div', 'a_Info')
        if a_info.find('span', 'a_source'):
          ly = a_info.find('span', 'a_source').text.strip()
        if a_info.find('span', 'a_time'):
          pb_time = a_info.find('span', 'a_time').text.strip()
        if a_info.find('span', 'a_author'):
          author = a_info.find('span', 'a_author').text.strip()
        if a_info.find('span', 'a_catelog'):
          category = a_info.find('span', 'a_catelog').text.strip()
      contents = main_content.find('div', 'bd')
      if contents:
        paras = contents.find_all('p')
        for para in paras:
          if para.find('img'):
            para_content_text_and_images.append(para.find('img')['src'].strip())
          else:
            p_text = para.text.strip()
            if len(p_text) > 0:
              para_content_text_and_images.append(p_text)
        if len(paras) == 0:
          if contents.find('div', 'Cnt-Main-Article-QQ'):
            brs = contents.find('div', 'Cnt-Main-Article-QQ')
            for br in brs.find_all('br'):
              br.replace_with('\n')
            para_content_text_and_images.extend(contents.find('div', 'Cnt-Main-Article-QQ')
                                                .text.strip().split('\n'))
    elif len(para_content_text_and_images) == 0:
      print("=" * 20, " >>> Empty contents. Try again... <<< ", "=" * 20)
      yield self.parse_dir_contents_selenium(response)
    else:
      print("=" * 20, " >>> Redirecting or with other news format... <<< ", "=" * 20)
      yield self.parse_dir_contents_selenium(response)
    item['url'] = url
    item['title'] = title
    item['pb_time'] = pb_time
    item['source'] = ly
    item['category'] = category
    item['para_content_text_and_images'] = para_content_text_and_images
    item['author'] = author
    item['reads'] = 0

    yield item

  def parse_gallery_picture(self, url):
    self.driver.get(url)
    time.sleep(5)
    # 通过强制的刷新操作基本解决图片和文本的更新
    self.driver.refresh()
    time.sleep(5)
    source = self.driver.page_source
    soup = BeautifulSoup(source, 'lxml')
    gallery = soup.find('div', 'galleryPic')
    ret_list = []
    if gallery.find('img'):
      ret_list.append(gallery.find('img')['src'].strip())
      print(gallery.find('img')['src'].strip())
    if soup.find('div', {'id': 'contTxt'}):
      texts = soup.find('div', {'id': 'contTxt'}).find_all('p')
      # print(texts)
      for ptext in texts:
        ret_list.append(ptext.text.strip())
    return ret_list
