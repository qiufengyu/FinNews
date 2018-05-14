# -*- coding: utf-8 -*-

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from spiders.wallstreet import WallStreetSpider
from spiders.hexun import HexunSpider
from spiders.eastmoney import EastMoneySpider
from spiders.sina_roll import SinaRollSpider
from spiders.tencent import TencentSpider

from wv.wordvec import WordVec

if __name__ == '__main__':
  settings = get_project_settings()
  process = CrawlerProcess(get_project_settings())
  # process.crawl(WallStreetSpider)
  # process.crawl(HexunSpider)
  # process.crawl(EastMoneySpider)
  # process.crawl(SinaRollSpider(pages=10))
  # process.crawl(TencentSpider)

  # process.start()
  w = WordVec()
  # w.write_documents()
  # w.train_wv()
  print(w.getvec("中国"))


