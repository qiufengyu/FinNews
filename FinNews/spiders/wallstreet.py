import re
import scrapy

from bs4 import BeautifulSoup

from items import WallStreetItem

class WallStreetSpider(scrapy.Spider):
    name = 'wallstreet'
    start_urls = [
        'https://wallstreetcn.com'
    ]

    def parse(self, response):
        soup = BeautifulSoup(response.body, 'lxml')
        for news_item in soup.find_all('div', 'article article-item'):
            sub_url = news_item.find('a')['href']
            if sub_url.startswith('http'):
                complete_url = sub_url
            else:
                complete_url = response.urljoin(sub_url)
            title = news_item.find('a', 'title').text.strip()
            summary = news_item.find('a', 'content').text.strip()
            source = None
            if news_item.find('div', 'left-item'):
                source = news_item.find('div', 'author').text.strip().replace(u'来源:','').strip()
            yield scrapy.Request(complete_url, callback=self.parse_dir_contents, meta={
                'title': title, 'summary': summary, 'source': source, 'sub_url': sub_url,
                'flag': sub_url.startswith('/a')
            })


    def parse_dir_contents(self, response):
        item = WallStreetItem()
        item['reads'] = 0
        item['likedby'] = []
        if 'wallstreet' not in response.url:
            return
        # 只抓取免费内容和华尔街的内容，跳转至其他平台的文章不获取
        if(response.meta['flag']):
            soup = BeautifulSoup(response.body, 'lxml')
            pb_time = soup.find('div', 'info').find('time', 'meta-item time').text.strip()
            para_content_text_and_images = []
            contents = soup.find('div', 'rich-text').find_all(re.compile('^[ph]'))
            for c in list(contents):
                if c.find('img'):
                    para_content_text_and_images.append(c.find('img')['src'].strip())
                else:
                    para_content_text_and_images.append(c.text.strip())
            item['title'] = response.meta['title']
            item['summary'] = response.meta['summary']
            item['source'] = response.meta['source']
            item['url'] = response.url
            item['pb_time'] = pb_time
            item['para_content_text_and_images'] = para_content_text_and_images
            yield item
        else:
            item['title'] = response.meta['title']
            item['summary'] = response.meta['summary']
            item['source'] = response.meta['source']
            if response.meta['sub_url'].startswith('/premium'):
                # 付费内容的 url
                item['url'] = 'https://wallstreetcn.com' + response.meta['sub_url']
            else:
                item['url'] = response.meta['sub_url']
            yield item


