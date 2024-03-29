# -*- coding: utf-8 -*-

# Scrapy settings for myscrapy project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'FinNews'

SPIDER_MODULES = ['FinNews.spiders']
NEWSPIDER_MODULE = 'FinNews.spiders'

# MongoDB settings
MONGO_HOST = "114.212.191.119"  # 主机IP
MONGO_PORT = 27017  # 端口号
MONGO_DBNAME = 'fin_news'
MONGO_COLLECTION_WALLSTREET = 'wallstreet'
MONGO_COLLECTION_HEXUN = 'hexun'
MONGO_COLLECTION_SINA = 'sina'
MONGO_COLLECTION_SINA_ROLL = 'sina_roll'
MONGO_COLLECTION_TENCENT = 'tencent'
MONGO_COLLECTION_EAST_MONEY_STOCK_LIST = 'east_money_stock_list'
MONGO_COLLECTION_EAST_MONEY_STOCK_MAP_USER = 'east_money_stock_map_user'
MONGO_COLLECTION_EAST_MONEY_STOCK_USER_INFO = 'east_money_stock_user_info'
MONGO_COLLECTION_EAST_MONEY_ARTICLE = 'east_money_article'
MONGO_COLLECTION_EAST_MONEY_ANNO = 'east_money_anno'
MONGO_COLLECTION_EAST_MONEY_RESEARCH_REPORT = 'east_money_research_report'
MONGO_COLLECTION_CANDIDATE = 'candidate'

# Sinajs to get real-time stocks
SINA_JS_STOCK_REQUEST = 'http://hq.sinajs.cn/list='

# Sina roll finance news
SINA_ROLL_FINANCE_NEWS = 'https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&k=&num=50&page={}'
SINA_ROLL_PAGES = 5
# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'myscrapy (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See http://scrapy.readthedocs.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 2.0
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'myscrapy.middlewares.MyscrapySpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#DOWNLOADER_MIDDLEWARES = {
#    'myscrapy.middlewares.MyCustomDownloaderMiddleware': 543,
#}
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'FinNews.middlewares.UserAgentMiddleware': 543,
}


# Enable or disable extensions
# See http://scrapy.readthedocs.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See http://scrapy.readthedocs.org/en/latest/topics/item-pipeline.html
#ITEM_PIPELINES = {
#    'myscrapy.pipelines.MyscrapyPipeline': 300,
#}
ITEM_PIPELINES = {
    'FinNews.pipelines.MongoPipeline': 300,
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See http://doc.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
