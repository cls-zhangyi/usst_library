import logging
from multiprocessing import Process
import pymysql
import requests
from lxml import etree
import json
from random import choice
import time

logger = logging.getLogger(__name__)
logger.setLevel(level = logging.INFO)
handler = logging.FileHandler("log.txt")
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
__process_list = []
db = pymysql.connect(host="localhost", user="root", password="", db="db_library", port=3306, charset='utf8')
cursor = db.cursor()
HEADERS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:57.0) Gecko/20100101 Firefox/57.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:58.0) Gecko/20100101 Firefox/58.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/604.5.6 (KHTML, like Gecko) Version/11.0.3 Safari/604.5.6',
]


def get_headers():
    headers = {
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': choice(HEADERS),
    }
    return headers


def f(name):
    baseurl="http://202.120.218.6:8080/browse/cls_browsing_book.php?s_doctype=all&cls="
    sql0 = "SELECT zid from tb_ztf where zid like '"+name+"%' and zid not in(select distinct item from tb_library) and zid not in (select zid from tb_ztf_book where num=0)"
    cursor.execute(sql0)
    source = cursor.fetchall()
    datas=[]
    for item in source:
        try:
            num=get_page(item[0])
        except Exception as e:
            print("error",e)
            continue
        if num >800:
            print(item,num)
            continue
        for page in range(1,num//7+2):
            try:
                url=baseurl+item[0]+"&page="+str(page)
            except Exception as e:
                print("error", e)
                continue
            datas=datas+get_item(url,item)
        if datas:
            data = tuple(datas)
            sql2 = 'INSERT INTO tb_library(bookname,cdesc,kind,store,lend,l2009,l2010,l2011,l2012,l2013,l2014,l2015,l2016,l2017,l2018,l2019,item) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
            cursor.executemany(sql2, data)
            db.commit()
            datas=[]


def get_page(item):
    url = "http://202.120.218.6:8080/browse/cls_browsing_book.php?s_doctype=all&cls=" + item
    html = requests.get(url=url, timeout=20, headers=get_headers())
    res = etree.HTML(html.text)
    nums = res.xpath('//div[@id="titlenav"]/font[3]')
    num = 0
    for nu in nums:
        num = nu.text
    data=(item, num)
    sql2 = 'INSERT INTO tb_ztf_book(zid,num) VALUES (%s,%s)'
    try:
        cursor.execute(sql2, data)
        db.commit()
    except:
        pass
    return int(num)


def get_item(url,x):
    datas=[]
    html = requests.get(url=url, timeout=20, headers=get_headers())
    res = etree.HTML(html.text)
    itemss = res.xpath('//div[@class="list_books"]//a')
    kindss = res.xpath('//div[@class="list_books"]//h3/text()')
    descss = res.xpath('//div[@class="list_books"]//p/text()')
    items=[]
    ids=[]
    kinds=[]
    descs=[]
    for item in itemss:
        items.append(item.text)
        ids.append(item.get('href', 'no=').split("no=")[-1])
    for kind in kindss:
        kinds.append(kind.strip())
    for desc in descss:
        descs.append(desc.strip())
    for i in range(0,len(ids)):
        id=ids[i]
        title=items[i]
        kind=kinds[i]
        desc=descs[2*i+1]
        st=store(id)
        sto=st.get("store",0)
        lend = st.get("lend", 0)
        his=history(id)
        data = [title,kind,desc,sto,lend]+his+[x[0]]
        print(data)
        datas.append(data)
    return datas


def history(id):
    baseurl="http://202.120.218.6:8080/opac/ajax_lend_trend.php?id="+str(id)
    html = requests.get(url=baseurl, timeout=20, headers=get_headers())
    js = json.loads(html.text)
    history=js.get("elements")[0].get("values")
    return history


def store(id):
    baseurl="http://202.120.218.6:8080/opac/ajax_lend_avl.php?marc_no="+str(id)
    html = requests.get(url=baseurl, timeout=20, headers=get_headers())
    res = etree.HTML(html.text)
    stores=res.xpath("//b")
    store={"store":0,"lend":0}
    for item in stores:
        store["store"]=item.text.split("/")[0]
        try:
            store["lend"] = item.text.split("/")[-1]
        except:
            pass
    return store


if __name__ == '__main__':
    print("ProgramStart")

    abc=list("ABCDEFGHIJKNOPQRSTUVXZ")
    for item in  list("FHIT"):
        process = Process(target=f, args=(item,))
        __process_list.append(process)
    for begin in __process_list:
        begin.start()
    for stop in __process_list:
        stop.join()
    print("Finish")