# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo
import logging

from datetime import datetime
from scrapy.utils.project import get_project_settings
from items import WallStreetItem, HexunItem, EastMoneyStockIdNameItem, EastMoneyStockMapUserItem, EastMoneyStockUserInfoItem


logger = logging.getLogger(__name__)


class MyscrapyPipeline(object):
    def process_item(self, item, spider):
        return item


class MongoPipeline(object):
    def __init__(self):
        self.settings = get_project_settings()
        self.client = pymongo.MongoClient(self.settings['MONGO_HOST'], self.settings['MONGO_PORT'])
        self.db = self.client[self.settings['MONGO_DBNAME']]
        self.wallstreet = self.db[self.settings['MONGO_COLLECTION_WALLSTREET']]
        self.wallstreet.ensure_index('url', unique=True)
        self.hexun = self.db[self.settings['MONGO_COLLECTION_HEXUN']]
        self.hexun.ensure_index('url', unique=True)
        self.east_money_stock_list = self.db[self.settings['MONGO_COLLECTION_EAST_MONEY_STOCK_LIST']]
        self.east_money_stock_list.ensure_index('stock_id', unique=True)
        self.east_money_stock_map_user = self.db[self.settings['MONGO_COLLECTION_EAST_MONEY_STOCK_MAP_USER']]
        self.east_money_stock_user_info = self.db[self.settings['MONGO_COLLECTION_EAST_MONEY_STOCK_USER_INFO']]

    def process_item(self, item, spider):
        if isinstance(item, WallStreetItem):
            try:
                self.wallstreet.insert_one(dict(item))
            except Exception as e:
                logger.warning('process_item.wallstreet: %s', str(item), exc_info=1)
        elif isinstance(item, HexunItem):
            try:
                self.hexun.insert_one(dict(item))
            except Exception as e:
                logger.warning('process_item.hexun: %s', str(item), exc_info=1)
        elif isinstance(item, EastMoneyStockIdNameItem):  # 东方财富 股票基金债券代码
            try:
                if not self.east_money_stock_list.find_one({'stock_id': item['stock_id']}):
                    ins = dict(item)
                    ins['stock_insert_time'] = datetime.now().strftime('%Y%m%d:%H')
                    self.east_money_stock_list.insert(ins)
            except Exception as e:
                logger.warning('process_item.EastMoneyStockIdNameItem: %s', str(item), exc_info=1)

        elif isinstance(item, EastMoneyStockMapUserItem):  # 东方财富，股票映射到股东
            try:
                self.east_money_stock_map_user.insert(dict(item))
            except Exception as e:
                logger.warning('process_item.EastMoneyStockMapUserItem: %s', str(item), exc_info=1)

        elif isinstance(item, EastMoneyStockUserInfoItem):  # 东方财富，股票的股东信息
            try:
                find_one = self.east_money_stock_user_info.find_one({'userid': item['userid']})
                if not find_one:
                    ins = dict(item)
                    ins['stockid_list'] = [item['stock_id']]
                    del ins['stock_id']
                    self.east_money_stock_user_info.insert(ins)
                else:
                    old = list(find_one['stockid_list'])
                    old.append(item['stock_id'])
                    self.east_money_stock_user_info.update({'userid': item['userid']}, {"$set": {"stockid_list": old}})
                    print(old)
            except Exception as e:
                logger.warning('process_item.EastMoneyStockIdNameItem: %s', str(item), exc_info=1)
        else:
            logger.warning("No pipe line item handler !")
            raise NotImplementedError
        return item
