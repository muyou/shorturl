#-*- coding: utf-8 -*-
import redis
import tornado.auth
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import unicodedata
import urllib.parse


from tornado.options import define, options
define("port", default=80, help="run on the given port", type=int)
define("dbhost", default="192.168.1.228", help="db host")
define("dbport", default=6379, help="db port", type=int)
define("dbname", default=1, help="db name", type=int)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/([^/]+)", HomeHandler)            
        ]
        settings = dict(
            blog_title=u"ShareBattle"
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        self.db = redis.StrictRedis(host=options.dbhost, port=options.dbport, db=options.dbname)

class HomeHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db
    
    def get(self,slug):            
        longurl = self.db.get('turl:'+slug).decode() if self.db.exists('turl:'+slug) else ''
        
        # 找不到重定向到 404
        if not longurl: raise tornado.web.HTTPError(404)
        #self.redirect(longurl, permanent=True)
        
        #通过模板在iframe里播放
        #self.render("templates/base.html", title='说唐战斗分享',longUrl=longurl)

        #print(longurl)
        self.write('原始网址是：%s' % longurl)

def main():
    #解析命令行参数
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
