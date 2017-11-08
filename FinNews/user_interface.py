import hashlib
import logging
import urllib.request

import pymongo
import pprint
from scrapy.utils.project import get_project_settings

from items import UserItem

logger = logging.getLogger(__name__)

class UserInterface(object):
    def __init__(self):
        self.settings = get_project_settings()
        self.client = pymongo.MongoClient(self.settings['MONGO_HOST'], self.settings['MONGO_PORT'])
        self.db = self.client[self.settings['MONGO_DBNAME']]
        self.candidate = self.db[self.settings['MONGO_COLLECTION_CANDIDATE']]
        self.stocklist = self.db[self.settings['MONGO_COLLECTION_EAST_MONEY_STOCK_LIST']]
        self.users = self.db.users
        self.users.ensure_index('user_name', unique=True)
        self.user = None

    def _insert_user(self, userItem):
        if isinstance(userItem, UserItem):
            try:
                exist = self.users.find_one({'user_name': userItem['user_name']})
                if exist:
                    return -3
                else:
                    self.users.insert_one(dict(userItem))
                    self.user = userItem
            except Exception as e:
                logger.warning('insert_user: %s', str(userItem), exc_info=1)
            return 1


    def add_user(self, user_password, user_name, recent_reads=[], tags=[], stocks=[]):
        user = UserItem()
        salt = 'nju'.encode('utf-8')
        user['user_password'] = hashlib.md5(user_password.encode('utf-8') + salt).hexdigest()
        user['user_name'] = user_name
        user['recent_reads'] = recent_reads
        user['tags'] = tags
        user['stocks'] = stocks
        return self._insert_user(user)

    def delete_user(self, user_id):
        """
        根据用户ID删除该用户，通过delete + insert 操作进行更新用户的密码信息
        :param self:
        :param user_id:
        :return:
        """
        r = self.users.delete_one({'user_id': user_id})
        return r.deleted_count


    def login(self, user_name, user_password):
        password = self.users.find_one({'user_name': user_name})
        if password is None:
            return -2
        salted = user_password.encode('utf-8') + 'nju'.encode('utf-8')
        if password['user_password'] == hashlib.md5(salted).hexdigest():
            self.user = password
            return 1
        else:
            return -1

    def start_up(self):
        q1 = int(input('Register 0 or Login 1：'))
        if q1 == 0:
            u_name = input('Set your user name: ')
            u_pwd1 = input('Set password: ')
            u_pwd2 = input('Input password again: ')
            while (u_pwd1 != u_pwd2):
                print("Password not consistant! Try again!")
                u_pwd1 = input('Set password: ')
                u_pwd2 = input('Input password again: ')
            return ui.add_user(user_password=u_pwd1, user_name=u_name)
        elif q1 == 1:
            u_name = input('User name: ')
            u_pwd = input('Password: ')
            r1 = self.login(u_name, u_pwd)
            if r1 > 0:
                print("Login OK!")
                return 1
            else:
                print("Login failed with error code {}".format(r1))
                return -1

    def read_news(self):
        user_entity = self.user
        recent_reads = user_entity['recent_reads']
        tags = user_entity['tags']
        stocks = user_entity['stocks']
        # 目前先推荐最新的新闻
        choice = 0
        while(choice >= 0 and choice < 10):
            news_cursor = self.candidate.find().sort('pb_time', pymongo.DESCENDING)
            news_list = []
            for news in news_cursor:
                news_list.append(news)
            print("-"*80)
            min_limit = 10 if len(news_list) > 10 else len(news_list)
            for i in range(min_limit):
                print("{}. {}, 发布时间：{}".format(i, news_list[i]['title'], news_list[i]['pb_time']))
                print("\t {}".format(news_list[i]['url']))
            print("-" * 80)
            print("Any other keys to exit...")
            try:
                choice = int(input("Select the news: "))
            except Exception as e:
                # logger.warning('Invalid choice', exc_info=1)
                return -1
            if(choice >= 0 and choice < min_limit):
                pprint.pprint(news_list[choice])
                # 更新最近读过的新闻
                news_read = [news_list[choice]['title']]
                if len(recent_reads) < 50:
                    recent_reads = news_read + recent_reads
                else:
                    recent_reads = news_read + recent_reads[-1]
                self.users.find_one_and_update({'user_name': user_entity['user_name']}, {'$set': {'recent_reads': recent_reads}})
                input("Press any key to back...")

    def read_stocks(self):
        user_entity = self.user
        home = self.settings['SINA_JS_STOCK_REQUEST']
        stocks = user_entity['stocks']
        for i, s in enumerate(stocks):
            req = urllib.request.Request(url=home+s)
            response = urllib.request.urlopen(req)
            data = response.read().decode("gbk").split(',')
            current = float(data[3])
            previous_close = float(data[2])
            delta = float(data[3]) -float(data[2])
            percent = 100.0 * delta / previous_close
            start_index = data[0].index('"') + 1
            name = data[0][start_index:]
            print("{}. {}\n当前价格：{:.2f}\t跌涨幅：{:+.2f} ({:+.2f})%".format(i+1, name, current, delta, percent))


    def modify_tags(self):
        user_entity = self.user
        tags = user_entity['tags']
        choice = 0
        while (choice >= 0):
            print("-" * 80)
            print("1. add a tag, \n2. delete a tag\nAny other key to quit")
            print("-" * 80)
            choice = input("Choice: ")
            try:
                choice = int(choice)
            except Exception as e:
                return 0
            if (choice == 1):
                tag = input("Your tag: ")
                tags.append(tag)
                tags = sorted(list(set(tags)))
                self.users.find_one_and_update({'user_name': user_entity['user_name']},
                                               {'$set': {'tags': tags}})
                print("{} added!".format(tag))
            elif choice == 2:
                print("-" * 80)
                for i, x in enumerate(tags):
                    print("{}. {} ".format(i + 1, x))
                print("-" * 80)
                del_choice = input("Delete with the number, quit with any other key: ")
                try:
                    del_choice = int(del_choice)
                    if len(tags) >= del_choice:
                        print("{} deleted.".format(tags[del_choice - 1]))
                        del tags[del_choice - 1]
                        self.users.find_one_and_update({'user_name': user_entity['user_name']},
                                                       {'$set': {'tags': tags}})
                except Exception as e:
                    print("Quitting...")
                    choice = 2
            else:
                return -4
        return 1

    def modify_stocks(self):
        user_entity = self.user
        stocks = user_entity['stocks']
        choice = 0
        while(choice >= 0):
            print("-" * 80)
            print("1. add with code or name, \n2. delete with code or name\nAny other key to quit")
            print("-" * 80)
            choice = input("Choice: ")
            try:
                choice = int(choice)
            except Exception as e:
                return 0
            if (choice == 1):
                stock_entity = None
                code_or_name = input("code or name: ")
                if code_or_name.startswith('sz') or code_or_name.startswith('sh'):
                    stock_entity = self.stocklist.find_one({'stock_id': code_or_name})
                    if stock_entity is not None:
                        stocks.append(code_or_name)
                        print("{} added!".format(stock_entity['stock_name']))
                    else:
                        print("No such stock! Error!")
                else:
                    stock_entity = self.stocklist.find_one({'stock_name': code_or_name})
                    if stock_entity is not None:
                        # pprint.pprint(stock_entity)
                        stocks.append(stock_entity['stock_id'])
                        print("{} added!".format(stock_entity['stock_name']))
                    else:
                        print("No such stock! Error!")
                # print(stocks)
                stocks = sorted(list(set(stocks)))
                # print(stocks)
                self.users.find_one_and_update({'user_name': user_entity['user_name']},
                                               {'$set': {'stocks': stocks}})
            elif choice == 2:
                print("-" * 80)
                for i, x in enumerate(stocks):
                    name = self.stocklist.find_one({'stock_id': x})
                    print("{}. {} {}".format(i+1, x, name['stock_name']))
                print("-" * 80)
                del_choice = input("Delete with the number, quit with any other key: ")
                try:
                    del_choice = int(del_choice)
                    if len(stocks) >= del_choice:
                        print("{} deleted.".format(stocks[del_choice - 1]))
                        del stocks[del_choice - 1]
                        stocks = sorted(list(set(stocks)))
                        self.users.find_one_and_update({'user_name': user_entity['user_name']},
                                                       {'$set': {'stocks': stocks}})
                except Exception as e:
                    print("Quitting...")
                    choice = 2
            else:
                return -4
        return 1


if __name__ == '__main__':
    ui = UserInterface()
    r0 = ui.start_up()
    choice = 0
    if r0 > 0: # 登录成功
        while(choice >= 0):
            print("="*80)
            print(" 1. Read news,\n 2. See stocks,\n 3. Modify personal tags, \n 4. Modify stocks. \n Any Other Key Exit")
            print("=" * 80)
            try:
                choice = int(input("Choice: "))
            except Exception as e:
                choice = -1
            if choice == 1:
                r1 = ui.read_news()
            elif choice == 2:
                r2 = ui.read_stocks()
            elif choice == 3:
                r3 = ui.modify_tags()
                if r3 < 0:
                    print("Modify over with code {}".format(r3))
            elif choice == 4:
                r4 = ui.modify_stocks()
                if r4 < 0:
                    print("Modify over with code {}".format(r4))
            else:
                break
        print('Bye!')
    else:
        print("Exit...")
        print("=" * 80)








