import datetime
import hashlib
import logging
import urllib.request

import pymongo
import pprint
from scrapy.utils.project import get_project_settings
from passlib.hash import django_pbkdf2_sha256

from items import UserItem
from utils.text_util import get_code2name

logger = logging.getLogger(__name__)


class UserDB(object):
  def __init__(self):
    self.settings = get_project_settings()
    self.client = pymongo.MongoClient(self.settings['MONGO_HOST'], self.settings['MONGO_PORT'])
    self.db = self.client[self.settings['MONGO_DBNAME']]
    self.users = self.db.users
    self.users.ensure_index('username', unique=True)

  def db_insert_user(self, userItem):
    if isinstance(userItem, UserItem):
      try:
        exist = self.users.find_one({'username': userItem['username']})
        if exist:
          return -3
        exist_email = self.users.find_one({'email': userItem['email']})
        if exist_email:
          return -4
        else:
          self.users.insert_one(dict(userItem))
      except Exception as e:
        logger.warning('insert_user: %s', str(userItem), exc_info=1)
      return 1

  def db_add_user(self, password, username, email, recent_reads_title=[], recent_reads_url=[], tags=[], stocks=[]):
    user = UserItem()
    user['password'] = django_pbkdf2_sha256.hash(password)
    user['username'] = username
    user['email'] = email
    user['recent_reads_title'] = recent_reads_title
    user['recent_reads_url'] = recent_reads_url
    user['tags'] = tags
    user['stocks'] = stocks
    return self.db_insert_user(user)

  def db_delete_user(self, username):
    """
    根据用户ID删除该用户，通过delete + insert 操作进行更新用户的密码信息
    :param self:
    :param user_id:
    :return:
    """
    r = self.users.delete_one({'username': username})
    return r.deleted_count

  def db_get_user(self, username):
    find_user = self.users.find_one({'username': username})
    return find_user if find_user else None

  def db_get_user_password(self, username):
    find_user = self.users.find_one({'username': username})
    if find_user:
      return find_user['password']
    else:
      return None

  def db_update_user_recent_reads_url(self, username, recent_reads_url):
    self.users.find_one_and_update({'username': username},
                                   {'$set': {'recent_reads_url': recent_reads_url}})

  def db_update_user_recent_reads_title(self, username, recent_reads_title):
    self.users.find_one_and_update({'username': username},
                                   {'$set': {'recent_reads_title': recent_reads_title}})

  def db_update_user_tags(self, username, tags):
    self.users.find_one_and_update({'username': username},
                                   {'$set': {'tags': tags}})

  def db_update_user_stocks(self, username, stocks):
    self.users.find_one_and_update({'username': username},
                                   {'$set': {'stocks': stocks}})


class UserInterface(object):
  def __init__(self, user, user_db):
    # 用户数据库
    self.user_db = user_db
    # 用户
    self.user = user
    self.settings = get_project_settings()
    self.client = pymongo.MongoClient(self.settings['MONGO_HOST'], self.settings['MONGO_PORT'])
    self.db = self.client[self.settings['MONGO_DBNAME']]
    self.candidate = self.db[self.settings['MONGO_COLLECTION_CANDIDATE']]
    self.stocklist = self.db[self.settings['MONGO_COLLECTION_EAST_MONEY_STOCK_LIST']]
    # 一些用户数据
    self.news_list = []  # 待推荐的新闻列表
    self.recent_reads_url = self.user['recent_reads_url']  #
    self.recent_reads_title = self.user['recent_reads_title']
    self.tags = self.user['tags']
    self.stocks = self.user['stocks']

  def get_candidate_news(self):
    # 目前先推荐最新的新闻
    news_cursor = self.candidate.find().sort('pb_time', pymongo.DESCENDING)
    for news in news_cursor:
      self.news_list.append(news)
    return self.news_list

  def update_recent_reads(self, news_title, news_url):
    """
    这里的（局部）变量 self.recent_reads 需要与数据库中的保持一致，
    进行推荐的时候就使用 self.recent_reads 进行推荐决策
    :param news_title: str
    :return: 
    """
    news_read_title = [news_title]
    news_read_url = [news_url]
    if len(self.recent_reads_title) < 50:
      self.recent_reads_title = news_read_title + self.recent_reads_title
      self.recent_reads_url = news_read_url + self.recent_reads_url
    else:
      self.recent_reads_title = news_read_title + self.recent_reads_title[:-1]
      self.recent_reads_url = news_read_url + self.recent_reads_url[:-1]
    # 更新数据库
    self.user_db.db_update_user_recent_reads_url(self.user['username'], self.recent_reads_url)
    self.user_db.db_update_user_recent_reads_title(self.user['username'], self.recent_reads_title)

  def read_stocks(self):
    home = self.settings['SINA_JS_STOCK_REQUEST']
    stocks_info = []
    for i, s in enumerate(self.get_stocks()):
      req = urllib.request.Request(url=home + s)
      response = urllib.request.urlopen(req)
      data = response.read().decode("gbk").split(',')
      current = float(data[3])
      previous_close = float(data[2])
      delta = float(data[3]) - float(data[2])
      if previous_close > 0:
        percent = 100.0 * delta / previous_close
      else:
        percent = 0.0
      start_index = data[0].index('"') + 1
      name = data[0][start_index:]
      stocks_info.append("{}. {}\n当前价格：{:.2f}\t跌涨幅：{:+.2f} ({:+.2f})%".format(
        i + 1, name, current, delta, percent))
    return stocks_info

  def add_tag(self, tag):
    self.tags.append(tag)
    self.tags = sorted(list(set(self.tags)))
    self.user_db.db_update_user_tags(self.user['username'], self.tags)

  def get_tags(self):
    self.tags = sorted(list(set(self.tags)))
    return self.tags

  def del_tag(self, index):
    if index <= len(self.tags):
      del self.tags[index - 1]
      self.user_db.db_update_user_tags(self.user['username'], self.tags)

  def add_stock(self, code_or_name):
    stock_entity = None
    new_stock_entity = {}
    if code_or_name.startswith('sz') or code_or_name.startswith('sh'):
	    stock_entity = self.stocklist.find_one({'stock_id': code_or_name})
	    if stock_entity is not None:
		    new_stock_entity['stock_id'] = stock_entity['stock_id']
		    new_stock_entity['datetime'] = datetime.datetime.now()
		    self.stocks.append(new_stock_entity)
    else:
	    stock_entity = self.stocklist.find_one({'stock_name': code_or_name})
	    if stock_entity is not None:
		    new_stock_entity['stock_id'] = stock_entity['stock_id']
		    new_stock_entity['datetime'] = datetime.datetime.now()
		    # pprint.pprint(stock_entity)
		    self.stocks.append(new_stock_entity)
    # print(stock_entity)
    self.user_db.db_update_user_stocks(self.user['username'], self.stocks)
    return stock_entity

  def get_stocks(self):
    self.stocks = sorted(self.stocks, key=lambda x: x['datetime'])
    stocks_id_list =[]
    for y in self.stocks:
	    stocks_id_list.append(y['stock_id'])
    return stocks_id_list

  def del_stock(self, index):
    if index <= len(self.stocks):
      del self.stocks[index - 1]
      self.user_db.db_update_user_stocks(self.user['username'], self.stocks)


if __name__ == '__main__':
  user_db = UserDB()
  user_entity = None

  while True:
    q1 = -1
    try:
      q1 = int(input('Register 0 or Login 1：'))
    except Exception as e:
      print("Invalid input, 0 and 1 are accepted.")
      continue
    # Register
    if q1 == 0:
      u_name = input('Set your user name: ')
      u_email = input('Set your email: ')
      u_pwd1 = input('Set password: ')
      u_pwd2 = input('Input password again: ')
      while u_pwd1 != u_pwd2:
        print("Password not consistent! Try again!")
        u_pwd1 = input('Set password: ')
        u_pwd2 = input('Input password again: ')
      reg = user_db.db_add_user(password=u_pwd1, username=u_name, email=u_email)
      if reg < 0:
        print("User name already exist, try again...")
      else:
        user_entity = user_db.db_get_user(u_name)
        break
    elif q1 == 1:
      u_name = input('User name: ')
      u_pwd = input('Password: ')
      password = user_db.db_get_user(u_name)
      if password is None:
        print("You are not registered! Please sign up first!")
      else:
        if django_pbkdf2_sha256.verify(u_pwd, password['password']):
          user_entity = password
          break
        else:
          print("Wrong password!")
    else:
      print("Invalid input, 0 and 1 are accepted.")

  assert (user_entity is not None)
  choice = 0

  ui = UserInterface(user_entity, user_db)
  while (choice >= 0):
    print("=" * 80)
    print(" 1. Read news,\n 2. See stocks,\n 3. Modify personal tags, \n 4. Modify stocks. \n Any Other Key Exit")
    print("=" * 80)
    try:
      choice = int(input("Choice: "))
    except ValueError as ve:
      choice = -1

    if choice == 1:
      while True:
        news_list = ui.get_candidate_news()
        print("-" * 80)
        min_limit = min(10, len(news_list))
        for i in range(min_limit):
          print("{}. {}, 发布时间：{}".format(i, news_list[i]['title'], news_list[i]['pb_time']))
          print("\t {}".format(news_list[i]['url']))
        print("-" * 80)
        print("Any other keys to exit...")
        try:
          sel = int(input("Select the news: "))
          if 0 <= sel and sel < min_limit:
            pprint.pprint(news_list[sel])
            ui.update_recent_reads(news_list[sel]['title'], news_list[sel]['url'])
            # user_db.db_update_user_recent_reads(user_entity['user_name'], news_list[sel]['title'])
            input("Input any key to back...")
        except ValueError as ve:
          # logger.warning('Invalid choice', exc_info=1)
          break
    elif choice == 2:
      print("-" * 80)
      stocks_info = ui.read_stocks()
      for i, s in enumerate(stocks_info):
        print(s)
      print("-" * 80)
      input("Input any key to back...")
    elif choice == 3:
      sel = 0
      while sel >= 0:
        print("-" * 80)
        print("1. add a tag, \n2. delete a tag\nAny other key to quit")
        print("-" * 80)
        sel_str = input("Choice: ")
        try:
          sel = int(sel_str)
        except ValueError as ve:
          break
        if (sel == 1):
          tag = input("Your tag (Press `Enter` to cancel): ")
          if len(tag) >= 1:
            ui.add_tag(tag.strip())
            print("{} added!".format(tag))
          else:
            print("Invalid tag {} for the `Enter`".format(tag))
        elif sel == 2:
          tags = ui.get_tags()
          print("-" * 80)
          for i, x in enumerate(tags):
            print("{}. {} ".format(i + 1, x))
          print("-" * 80)
          del_index = input("Delete with the number, quit with any other key: ")
          try:
            del_index = int(del_index)
            if len(tags) >= del_index:
              print("{} deleted.".format(tags[del_index - 1]))
              ui.del_tag(del_index)
            else:
              print("Input out of range max {}".format(len(tags)))
          except ValueError as ve:
            # 不退出，回到编辑个性化标签的主界面
            sel = 2
        else:
          break
    elif choice == 4:
      sel = 0
      code2name = get_code2name()
      while (sel >= 0):
        print("-" * 80)
        print("1. add with code or name, \n2. delete with code or name\nAny other key to quit")
        print("-" * 80)
        sel_str = input("Choice: ")
        try:
          sel = int(sel_str)
        except ValueError as ve:
          # logger.warning('Invalid choice', exc_info=1)
          break
        if sel == 1:
          code_or_name = input("code or name (Press `Enter` to cancel): ")
          if len(code_or_name) >= 1:
            stock_item = ui.add_stock(code_or_name)
            if stock_item:
              print("{} added".format(stock_item['stock_name']))
            else:
              print("Invalid code or name the stock {}".format(code_or_name))
        elif sel == 2:
          stocks = ui.get_stocks()
          print("-" * 80)
          for i, x in enumerate(stocks):
            print("{}. {} {}".format(i + 1, x, code2name[x]))
          print("-" * 80)
          del_index = input("Delete with the number, quit with any other key: ")
          try:
            del_index = int(del_index)
            if len(stocks) >= del_index:
              print("{} - {} deleted.".format(stocks[del_index - 1], code2name[stocks[del_index - 1]]))
              ui.del_stock(del_index)
            else:
              print("Input out of range max {}".format(len(stocks)))
          except ValueError as ve:
            # 不退出，回到编辑自选股的主界面
            sel = 2
        else:
          break
    else:
      break
  print('Bye!')

  print("Exit...")
  print("=" * 80)
