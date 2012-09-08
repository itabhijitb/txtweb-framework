'''
Created on Aug 30, 2012

@author: abhibhat
'''
import jinja2
import urllib, urllib2
import os
import webapp2
from collections import namedtuple
from google.appengine.api import memcache
import cgi
from BeautifulSoup import BeautifulSoup
try:
    file_path = os.path.dirname(__file__)
except NameError:
    file_path = "."
jinja_environment = jinja2.Environment(
       loader=jinja2.FileSystemLoader(file_path))
template = jinja_environment.get_template('index.html')
class Txt2Web(webapp2.RequestHandler):
    '''
    Python framework to create txt2web application. 
    '''
    template = jinja_environment.get_template('index.html')
    form = namedtuple('forms',['action','name','text'])
    hrefs = namedtuple('hrefs',['parms','text'])
    chart = namedtuple('chart',['title','resp_count','data'])
    dropbox = namedtuple('dropbox',['title','choices'])
    dropboxes = namedtuple('dropboxes',['name','password','dropbox'])
    host = "http://top-fund.appspot.com"
    txtweb_number = "9243342000"
    def init(self,title,appkey):
        self.template_values = {
            'title': "Top Performing Fund",
            'appkey': "8a53f225-ab16-44b1-a239-aefaab198247",
            'body': "Invalid Session",
        }
        self.template_values['title'] = title
        self.template_values['appkey'] = appkey
        self.template_values['host']=urllib.splitquery(self.request.url)[0]
        self.first_time = self.request.get("txtweb-message")
        self.txtweb_mobile = self.request.get("txtweb-mobile")
        self.txtweb_message = self.request.get("txtweb-message")
        self.txtweb_password = self.request.get("txtweb-password")
        if self.first_time:
            self.save(("query", urllib.splitquery(self.request.url)[-1]))
    def write(self, body,hrefs=None):
        self.template_values['body'] = body
        self.template_values['hrefs'] = hrefs
        self.response.write(self.template.render(self.template_values))
    def connect(self,url,proxy=None,form=None):
        if form:
            form = urllib.urlencode(form)
        try:
            proxy = urllib2.ProxyHandler(proxy)
        except AssertionError:
            proxy = urllib2.ProxyHandler(None)
        req_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.A.B.C Safari/525.13',
            'Referer': 'http://python.org'}
        request = urllib2.Request(url, headers=req_headers)
        opener = urllib2.build_opener(proxy)
        response = opener.open(request,form)  
        self.code = response.code
        self.headers = response.headers
        self.content = response.read()
        self.soup = BeautifulSoup(self.content)
        
    def __getitem__(self,key):
        qs = self.retrieve("query")
        try:
            return cgi.parse_qs(qs)[key][0]
        except (KeyError, AttributeError) as e:
            return None
    def push(self,mobile,message):
        encoded_message = urllib.urlencode({"txtweb-mobile":mobile,
                                            "txtweb-message":message,
                                            "txtweb-pubkey":"8e717273-63f5-40ec-b3ca-295f404ba540"
                                            })  
        response = urllib.urlopen("http://api.txtweb.com/v1/push",data= encoded_message) 
                       
    def save(self,(key,value),timeout=60*5):
        return memcache.set(key,value,timeout,namespace=self.txtweb_mobile)
    def retrieve(self,key):
        return memcache.get(key,namespace=self.txtweb_mobile)
    def getitem(self,body,key,part_size=160):
        hrefs = [namedtuple('hrefs',['parms','text'])(["option=Next{}","txtweb-mobile="+self.txtweb_mobile],"Prev?"),
                 namedtuple('hrefs',['parms','text'])(["option=Next{}","txtweb-mobile="+self.txtweb_mobile],"Next?")]
        result = [[]]
        size = 0
        for e in body:
            if size + len(e) >= part_size:
                result.append([])
                size = 0
            size += len(e)
            result[-1].append(e)
        if key:
            hrefs[0].parms[0] = hrefs[0].parms[0].format(key - 1)
        else:
            query_str = self.retrieve("query")
            if query_str:
                hrefs[0][0][0] = query_str
                del hrefs[0][0][-1]
            else:
                del hrefs[0]
        if key < len(result) - 1:
            hrefs[-1].parms[0] = hrefs[-1].parms[0].format(key + 1)
        else:
            query_str = self.retrieve("query")
            if query_str:
                hrefs[-1][0][0] = query_str
                del hrefs[1][0][-1]
            else:
                del hrefs[-1]
        if not hrefs:  hrefs = None
        return result[key],hrefs