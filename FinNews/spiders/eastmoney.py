# -*- coding: utf-8 -*-
import scrapy
import logging
from scrapy.utils.response import get_base_url, open_in_browser
from bs4 import BeautifulSoup
from utils.text_util import *
from items import *
from functools import partial
import traceback
import json


logger = logging.getLogger(__name__)

def gen_code_url2parse():
    res = {}
    for code in get_code2name().keys():
        url = 'http://quote.eastmoney.com/' + code + '.html'
        if code[2] == '2':  # 债券
            res[url] = 'self.parse_bond_info'
            pass
        elif code[2] == '5':  # 基金
            res[url] = 'self.parse_fund_info'
            pass
        else:   # 股票
            res[url] = 'self.parse_stock_info'
            pass
    return res


# 首先从 http://quote.eastmoney.com/stocklist.html#sz 爬取股票代码，然后分别爬取有趣的东西
class EastMoneySpider(scrapy.Spider):
    name = 'eastmoney'
    allowed_domains = ['eastmoney.com']

    url_map_parse = {
        'http://quote.eastmoney.com/stocklist.html': 'self.parse_stocklist',
    }
    url_map_parse.update(gen_code_url2parse())
    start_urls = url_map_parse.keys()

    def parse(self, response):
        url = get_base_url(response)
        if url not in EastMoneySpider.url_map_parse:
            logger.warning(url + ' not in EastMoneySpider.url_map_parse')
            return
        return eval(EastMoneySpider.url_map_parse[url])(response)

    def parse_stocklist(self, response):
        soup = BeautifulSoup(response.body, "html5lib")
        for a_tag in soup.find('div', 'quotebody').findAll('a'):
            if 'href' not in a_tag.attrs:
                continue
            tx = a_tag.attrs['href']
            tx = tx[tx.rfind(u'/') + 1:tx.rfind('.html')]
            if len(tx) != 8:
                continue
            id_name = EastMoneyStockIdNameItem()
            txt = a_tag.get_text()
            id_name['stock_market'] = tx[:2]
            id_name['stock_name'] = txt[:txt.rfind(u'(')]
            id_name['stock_id'] = tx[2:]

            # print tx + ": " + txt[:txt.rfind(u'(')]
            # print a_tag.attrs['href']

            # 抓取公司股东的个人信息 正式跑的时候才解注释 只是抓取一次
            # req_url = 'http://emweb.securities.eastmoney.com/PC_HSF10/CompanyManagement/CompanyManagementAjax?code=' + tx
            # yield scrapy.Request(req_url, callback=self.parse_userinfo_json)

            # 转移到外部
            # if int(id_name['stock_id'][0]) == 2:  # 债券 抓取：债券要闻-债市分析-债券公告
                 # yield scrapy.Request(a_tag.attrs['href'], callback=self.parse_bond_info)
            # print 'source: ', a_tag.attrs['href'], id_name['stock_id']
            # if int(id_name['stock_id'][0]) == 5:  # 基金
                 # pass
            # else:  # 股票 抓取： 个股要闻-行业要闻-公司公告-个股研报-行业研报
                 # print id_name['stock_id']
                 # yield scrapy.Request(a_tag.attrs['href'], callback=self.parse_stock_info)
                 # pass
        return


    # 基金 抓取： 基金新闻-基金公告
    def parse_fund_info(self, response):
        # print len(EastMoneySpider.start_urls), 'http://www.eastmoney.com' in EastMoneySpider.start_urls
        _id = get_base_url(response)[-11:-5]
        soup = BeautifulSoup(response.body, "html5lib")

        report_tag = soup.find('div', attrs={'class': 'report '})
        if report_tag is None:
            return

        news_tag = report_tag.find('div', attrs={'class': 'news_list fl'})
        for a_tag in news_tag.findAll('a'):     # 基金新闻
            if 'title' not in a_tag.attrs:
                continue
            info_map = {'id': _id}
            info_map['title'] = a_tag.attrs['title']
            info_map['type'] = 'fund_news'
            yield scrapy.Request(a_tag.attrs['href'], callback=partial(self.parse_article, info_map))

        # 基金公告 的格式与其他公告（股票，债券）不同，暂不抓取
        # anno_tag = report_tag.find('div', attrs={'class': 'news_list mL10 fr'})
        # for a_tag in anno_tag.findAll('a'):     # 基金公告
        #     if 'title' not in a_tag.attrs:
        #         continue
        #     info_map = {'id': _id}
        #     info_map['title'] = a_tag.attrs['title']
        #     info_map['type'] = 'fund_anno'
        #     yield scrapy.Request(a_tag.attrs['href'], callback=partial(self.parse_annocement, info_map))
        pass



    # 股票 抓取： 个股要闻-行业要闻-公司公告-个股研报-行业研报
    def parse_stock_info(self, response):
        # print get_base_url(response)
        _id = get_base_url(response)[-11:-5]
        soup = BeautifulSoup(response.body, "html5lib")

        dv = soup.find('div', attrs={'class': 'layout mt10'})
        if dv is None:
            return

        for div_t in dv.findAll('div', attrs={'class': 'fl w390 mb10'}):  # 个股要闻-行业要闻 - 个股研报
            if u'个股要闻' in div_t.get_text():
                for a_tag in div_t.findAll('a'):  # 个股要闻-行业要闻
                    if 'title' not in a_tag.attrs:
                        continue
                    info_map = {'id': _id}
                    info_map['title'] = a_tag.attrs['title']
                    info_map['type'] = 'stock_news'
                    yield scrapy.Request(a_tag.attrs['href'], callback=partial(self.parse_article, info_map))
                pass
            elif u'个股研报' in div_t.get_text():
                table_tag = div_t.find('table', attrs={'class': 'linehleft w100p'})
                for tr_tag in table_tag.findAll('tr'):
                    td_tag_all = tr_tag.findAll('td')
                    if len(td_tag_all)!=3 or u'机构' in tr_tag.get_text():
                        continue
                    info_map = {}
                    info_map['type'] = u'个股研报'
                    info_map['ji_gou'] = td_tag_all[0].get_text()
                    info_map['ping_ji'] = td_tag_all[1].get_text()
                    info_map['time'] = td_tag_all[2].find('span', attrs={'class': 'dt'}).get_text()
                    info_map['title'] = td_tag_all[2].find('a').get_text()
                    yield scrapy.Request(td_tag_all[2].find('a').attrs['href'], callback=partial(self.parse_research_report, info_map))
                pass

        for div_t in dv.findAll('div', attrs={'class': 'fr w390 mb10'}):    # 公司公告 - 行业研报
            if u'公司公告' in div_t.get_text():
                for a_tag in div_t.findAll('a'):  # 个股要闻-行业要闻
                    if 'title' not in a_tag.attrs:
                        continue
                    info_map = {'id': _id}
                    info_map['title'] = a_tag.attrs['title']
                    info_map['type'] = 'stock_trade_news'
                    yield scrapy.Request(a_tag.attrs['href'], callback=partial(self.parse_annocement, info_map))
                pass
            elif u'行业研报' in div_t.get_text():
                table_tag = div_t.find('table', attrs={'class': 'linehleft w100p txtUL'})
                for tr_tag in table_tag.findAll('tr'):
                    td_tag_all = tr_tag.findAll('td')
                    if len(td_tag_all)!=3 or u'机构' in tr_tag.get_text():
                        continue
                    info_map = {}
                    info_map['type'] = u'行业研报'
                    info_map['ji_gou'] = td_tag_all[0].get_text()
                    info_map['ping_ji'] = td_tag_all[1].get_text()
                    info_map['time'] = td_tag_all[2].find('span', attrs={'class': 'dt'}).get_text()
                    info_map['title'] = td_tag_all[2].find('a').get_text()
                    yield scrapy.Request(td_tag_all[2].find('a').attrs['href'], callback=partial(self.parse_research_report, info_map))
                pass
                # print '行业研报'

        pass


    # 研报
    def parse_research_report(self, infomap, response):
        # print get_base_url(response)
        # print infomap
        url = get_base_url(response)
        soup = BeautifulSoup(response.body, "html5lib")
        report_info = soup.find('div', attrs={'class': 'report-infos'})
        author = report_info.findAll('span')[-1].get_text()

        report_body = soup.find('div', attrs={'class':'report-body Body', 'id':'ContentBody'})
        img_k_url = img_k_alt = ''  # 对于 个股研报
        two_img_url = ['', '']      # 对于 行业研报
        if infomap['type'] == u'个股研报':
            stock_img = report_body.find('p', attrs={'style':'text-align: center;text-indent:0em;'})
            img_tag = stock_img.find('img', attrs={'border':'0'})
            img_k_url = img_tag.attrs['src']
            img_k_alt = img_tag.attrs['alt']
        elif infomap['type'] == u'行业研报':
            two_img_url[0] = report_body.find('div', attrs={'class':'report-img-cont img-chart1'}).find('img').attrs['src']
            two_img_url[1] = report_body.find('div', attrs={'class': 'report-img-cont img-chart2'}).find('img').attrs['src']
        else:
            # print 'falssse'
            return

        # print stock_img
        # img_price_tips = stock_img.find('div', attrs={'class':'imgPriceTips'}).get_text()

        # 正文
        article_content = report_body.find('div', attrs={'class': 'newsContent'})
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
                else:
                    para_content_text_and_images.append(('', im.attrs['src']))
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

        item = EastMoneyResearchReportItem()
        item['url'] = url
        item['title'] = infomap['title']
        item['pb_time'] = infomap['time']
        item['ping_ji'] = infomap['ping_ji']
        item['ji_gou'] = infomap['ji_gou']
        item['author'] = author
        item['img_k_url'] = img_k_url
        item['img_k_alt'] = img_k_alt
        item['two_img_url'] = two_img_url
        item['research_report_type'] = infomap['type']
        # item['img_price_tips'] = img_price_tips
        item['para_content_text_and_images'] = para_content_text_and_images
        # print(dict(item))
        yield item


    # 债券 抓取：债券要闻-债市分析-债券公告
    def parse_bond_info(self, response):
        _id = get_base_url(response)[-11:-5]
        soup = BeautifulSoup(response.body, "html5lib")
        # print get_base_url(response)
        news_and_analyze = soup.find('div', attrs={'class': 'news_list tabExchangeCon'})
        if news_and_analyze is None:
            return

        for a_news_or_analyze in news_and_analyze.findAll('a'):  # 解析 债券要闻 债市分析
            if 'title' not in a_news_or_analyze.attrs:
                continue
            info_map = {'id': _id}
            info_map['title'] = a_news_or_analyze.attrs['title']
            info_map['type'] = 'bond_news'
            yield scrapy.Request(a_news_or_analyze.attrs['href'], callback=partial(self.parse_article, info_map))

        for a_announce in soup.find('div', attrs={'class': 'news_list mL10 fr'}).findAll('a'):
            if 'title' not in a_announce.attrs:
                continue
            info_map = {'id': _id}
            info_map['title'] = a_announce.attrs['title']
            info_map['type'] = 'bond_announce'
            yield scrapy.Request(a_announce.attrs['href'], callback=partial(self.parse_annocement, info_map))
        pass


    # 解析 公告
    def parse_annocement(self, infomap, response):
        url = get_base_url(response)
        # print url, infomap['title']
        soup = BeautifulSoup(response.body, "html5lib")

        content_tag = soup.find('div', attrs={'class': 'content'})
        anno_time = content_tag.find('div', attrs={'style':'text-align: right; margin-right: 50px;'}).get_text()
        source_pdf_url = content_tag.find('a', attrs={'style':'color: #039; text-decoration: underline; font-family: 宋体; font-size: 14px; display: inline-block;'}).attrs['href']
        content = content_tag.find('div', attrs={'style':'font-size: 14px; line-height: 164.28%; overflow-wrap: break-word; word-wrap: break-word; white-space: pre-wrap;'}).get_text()

        item = EastMoneyAnnounceItem()
        item['url'] = url
        item['title'] = infomap['title']
        item['type'] = infomap['type']
        item['anno_time'] = anno_time
        item['source_pdf_url'] = source_pdf_url
        item['content'] = content
        # print(dict(item))
        yield item


    # 解析 新闻
    # http: // finance.eastmoney.com / news / 1347, 20171103798537859.html
    def parse_article(self, infomap, response):
        url = get_base_url(response)
        print(url, infomap['title'])
        title = infomap['title']
        soup = BeautifulSoup(response.body, "html5lib")

        cur_source = []
        for a_tag in soup.find('div', attrs={'id': 'Column_Navigation'}).findAll('a'):
            cur_source.append(a_tag.get_text())

        left_content = soup.find('div', attrs={'class': 'left-content'})

        info_div = left_content.find('div', attrs={'class': 'Info'})
        pb_time = info_div.find('div', attrs={'class': 'time'}).get_text()

        source_tag = info_div.find('div', attrs={'class': 'source'})
        if source_tag.find('img') is not None:
            source = source_tag.find('img').attrs['alt']
        else:
            source = source_tag.get_text()

        author = editor = ''
        author_tag = info_div.find('div', attrs={'class': 'author'})
        if author_tag is not None:
            author = author_tag.get_text()
        for span_tag in info_div.findAll('span'):
            if u'编辑' not in span_tag.get_text():
                continue
            editor = span_tag.find('a').get_text()

        comment_list = [-1, -1]  # 4人评论 2211人参与讨论
        comment_div = left_content.find('div', attrs={'class': 'AboutCtrl'})
        span_cnum_show_num = comment_div.find('span', attrs={'class': 'cNumShow num'})
        span_num_ml5 = comment_div.find('span', attrs={'class': 'num ml5'})
        comment_list[0] = span_cnum_show_num.get_text() if span_cnum_show_num is not None else -1
        comment_list[1] = span_num_ml5.get_text() if span_num_ml5 is not None else -1
        # print comment_list

        # 正文
        article_content = soup.find('div', attrs={'id': 'ContentBody', 'class': 'Body'})
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
                else:
                    para_content_text_and_images.append(('', im.attrs['src']))
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

        # print '\n'.join(para_content_text_and_images)
        article_item = EastMoneyArticleItem()
        article_item['url'] = url
        article_item['cur_source'] = cur_source
        article_item['title'] = title
        article_item['type'] = infomap['type']
        article_item['pb_time'] = pb_time
        article_item['source'] = source
        article_item['author'] = author
        article_item['editor'] = editor
        article_item['comment_list'] = comment_list
        article_item['para_content_text_and_images'] = para_content_text_and_images
        # print(dict(article_item))
        yield article_item


    # 抓取公司股东的个人信息
    def parse_userinfo_json(self, response):
        stock_id = get_base_url(response)[-8:]
        userid_list = []
        json_data = json.loads(response.body, encoding='utf8')
        for one_man in json_data['Result']['RptManagerList']:
            name = one_man['xm']
            sex = one_man['xb']
            age = one_man['nl']
            edu = one_man['xl']
            duty = one_man['zw']
            start_time = one_man['rzsj']
            intro = one_man['jj']
            user_id = str(hash(name) % 100000) + str(hash(sex) % 10) + str(hash(age) % 100) + str(hash(edu) % 1000)

            yield EastMoneyStockUserInfoItem({'userid': user_id, 'name': name, 'sex': sex, 'edu': edu, 'age': age, \
                                              'duty': duty, 'start_time': start_time, 'intro': intro,
                                              'stock_id': stock_id, })
            userid_list.append(user_id)
        yield EastMoneyStockMapUserItem({'stock_id': stock_id, 'userid_list': userid_list})
