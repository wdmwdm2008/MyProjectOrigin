# coding:utf-8

from flask import request, render_template, jsonify,Blueprint
from threading import Timer
import pymysql
import random
import gc
import re
from APP.SpeechExtraction.news_extraction import My_Extractor

app_extraction = Blueprint("news_extraction", __name__, static_folder='static',template_folder='templates')


Extractor = None
engine =None

def load_extractor():
    global Extractor
    global engine
    if not Extractor:
        Extractor = My_Extractor() # 删除该对象时限调用对象的release方法
        print('模型载入')
    if not engine:
        engine = connet_sql()

def release_model():
    global Extractor
    global engine
    if Extractor:
        Extractor.release()
        _ = gc.collect()
        Extractor  = None
        _ = gc.collect()
        print('模型被释放')
    if engine:
        engine.close()
        engine = None
        _ = gc.collect()

def connet_sql():
    conn = pymysql.connect(
        host='rm-8vbwj6507z6465505ro.mysql.zhangbei.rds.aliyuncs.com',
        user='root',
        password='AI@2019@ai',
        db='stu_db',
        charset='utf8'
    )
    return conn

class DelayRelease:
    #用来延迟释放模型
    def timer_start(self):
        #使用后5分钟后释放模型
        self.t = Timer(300, release_model)
        self.t.start()
    def timer_stop(self):
        self.t.cancel()

Mytimer = DelayRelease()
@app_extraction.route("/", methods=["GET"])
def index():
    """定义的视图函数"""
    t = Timer(1, load_extractor)
    t.start()
    return render_template("pro1.html")

@app_extraction.route("/solve", methods=["POST"])
def solve():
    text = request.data
    if isinstance(text, bytes):
        text = text.decode('utf-8')
    text = text.replace('\u3000', '')
    text = text.replace('\\n', '')
    text = text.replace(' ', '')
    # print(text)
    if Extractor:
        try:
            data = Extractor.get_results(text)
        except:
            return jsonify({'code':0})

        try:Mytimer.timer_stop()
        except:pass
        Mytimer.timer_start()
        return jsonify(data)
    else:
        return jsonify({'code': 0})

@app_extraction.route("/mysql", methods=["GET"])
def get_data_mysql():
    if engine:
        rnd = random.randint(21000,41999)
        sql = "select content from news_chinese_01 where id="+str(rnd)
        cur = engine.cursor()
        cur.execute(sql)
        ss = cur.fetchall()[0][0].replace('\\n','')
        title =-1
        for flag in ('乐讯','报讯','快讯','技讯','日电','日讯','(组图)', '(图)','（组图）','（图）'):
            title =  ss.find(flag)
            if title != -1:
                title = (title, title+len(flag))
                break
        if title ==-1:
            title = re.search(r'[\(（]\w*?记者.*?[\)）]', ss)
            if title:
                title =title.span()
            else:
                title = -1
        if title != -1:
            content = ss[title[1]:]
            head = ss[:title[0]]
        else:
            content = ss
            head = ''
        data = {'content':content,'title':head}
        return jsonify(data)
