import requests
import redis
import json
import time
from lxml import etree
import pymysql

db = pymysql.connect(host="localhost", user="root", password="", db="db_library", port=3306, charset='utf8')
cursor = db.cursor()
base_url = "http://202.120.218.6:8080/browse/cls_browsing_tree.php?s_doctype=all&cls="
clss="ABCDEFGHIJKNOPQRSTUVXZ"
values = []
index=[]
for lvl in range(1,7):
    for cls in clss:
        time.sleep(1)
        url=base_url+cls+"&lvl="+str(lvl)
        try:
            html = requests.get(url=url,timeout=20)
            print(html.status_code)
        except Exception as e:
            print("error",e)
        res = etree.HTML(html.text)
        zids = res.xpath("//span[@style='cursor:hand;']")
        for item in zids:
            zid=item.text.split(" ", 1)[0]
            des = item.text.split(" ", 1)[-1]
            if zid in index:
                continue
            index.append(zid)
            values.append([
        zid,
        des])
            print(zid)
        zidss = res.xpath("//a[@style='cursor:hand;']")
        for item in zidss:
            zid=item.text.split(" ",1)[0].replace("-",".")
            des = item.text.split(" ",1)[-1]
            if zid in index:
                continue
            index.append(zid)
            values.append([
        zid,
        des])
            print(zid)
value = tuple(values)
sql2 = 'INSERT INTO tb_ztf VALUES (%s,%s)'
cursor.executemany(sql2, value)
db.commit()