#-*- coding: utf-8 -*-
import hashlib
import json
import os
import os.path
import random
import re
import redis
import time
import tornado.auth
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import unicodedata



from tornado.options import define, options

define("port", default=9001, help="run on the given port", type=int)
define("dbhost", default="192.168.1.228", help="db host")
define("dbport", default=6379, help="db port", type=int)
define("dbname", default=1, help="db name", type=int)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/create", CreateHandler)          
        ]
        settings = dict(
            blog_title=u"ShareBattle"
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        self.db = redis.StrictRedis(host=options.dbhost, port=options.dbport, db=options.dbname)

class CreateHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db

    def get(self):
        urls = self.db.keys('*')
        ret = {}        
        for url in urls:
            key = url.decode()
            if key.startswith('turl:'):
                ret[key[5:]] = self.db.get(key).decode()
        ret_json = json.dumps(ret,sort_keys=True,ensure_ascii=False,indent=4)
        self.write(ret_json)
        
    def post(self):        
        longUrl = self.get_argument('url')        
        tinyUrl_list = get_hash_key(longUrl)

        for tmp_url in tinyUrl_list:
            if self.db.exists('turl:'+tmp_url):
                if self.db.get('turl:'+tmp_url).decode() == longUrl:
                    return self.create_reponse(status=-2,err_msg='已经存在',tinyurl='http://zd.jy1000.com/' + tmp_url)
                else:
                    tinyUrl_list.remove(tmp_url)
            else:
                continue
            
        
        tinyUrl = tinyUrl_list[random.randint(0,len(tinyUrl_list)-1)]
        
        ok = False
        if self.db.exists('turl:'+tinyUrl) :
            return self.create_reponse(status=-2,err_msg='已经存在')
        else :
            ok = self.db.set('turl:'+tinyUrl,longUrl)
            self.db.rpush('turl:list', tinyUrl)      
            if ok :
                return self.create_reponse(status=0,tinyurl='http://zd.jy1000.com/' + tinyUrl)
            else :
                return self.create_reponse(status=-1,err_msg='生成错误')
      

    def create_reponse(self,status,tinyurl='',longurl='',err_msg=''):
        ret = {}
        ret['err_msg'] = err_msg   
        ret['longurl'] = longurl
        ret['tinyurl'] = tinyurl
        ret['status'] = status
        ret_json = json.dumps(ret,sort_keys=True,ensure_ascii=False)
        self.write(ret_json)
        
'''
other method
'''
code_map = ( 
           'a' , 'b' , 'c' , 'd' , 'e' , 'f' , 'g' , 'h' , 
           'i' , 'j' , 'k' , 'l' , 'm' , 'n' , 'o' , 'p' , 
           'q' , 'r' , 's' , 't' , 'u' , 'v' , 'w' , 'x' , 
           'y' , 'z' , '0' , '1' , '2' , '3' , '4' , '5' , 
           '6' , '7' , '8' , '9' , 'A' , 'B' , 'C' , 'D' , 
           'E' , 'F' , 'G' , 'H' , 'I' , 'J' , 'K' , 'L' , 
           'M' , 'N' , 'O' , 'P' , 'Q' , 'R' , 'S' , 'T' , 
           'U' , 'V' , 'W' , 'X' , 'Y' , 'Z'
            ) 

def get_md5(s): 
    s = s.encode('utf-8')
    m = hashlib.md5()
    m.update(s)
    return m.hexdigest()
      
def get_hash_key(long_url): 
    hkeys = []
    hex = get_md5(long_url)
    for i in range(0, 4):
        n = int(hex[i*8:(i+1)*8], 16)
        v = []
        e = 0
        for j in range(0, 5):
            x = 0x0000003D & n
            e |= ((0x00000002 & n ) >> 1) << j
            v.insert(0, code_map[x])
            n = n >> 6
        e |= n << 5
        v.insert(0, code_map[e & 0x0000003D])
        hkeys.append(''.join(v))

    return hkeys



def main():
    #解析命令行参数
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
