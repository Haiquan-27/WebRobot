from urllib import request,parse
from http import cookiejar
import ssl
from io import BytesIO
import gzip
import random
import time

__version = "0.1"
__all__ = ["WebRobot"]

class WebRobot():
	def __init__(self):
		self.timeout = 4
		self.headers = {
			# "Host": "",
			# "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
			# "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
			# "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
			# "Accept-Encoding": "gzip, deflate",
			# "Connection": "close",
			# "Cookie": "",
			# "Upgrade-Insecure-Requests": "1",
		}
		self.default_encodeing = "UTF8"
		self.global_proxy = {
			"https":"127.0.0.1:8080",
			"http":"127.0.0.1:8080"
		}
		self.ssl_verify = ssl._create_unverified_context() # 不验证未经过CA认证的站点
		self.handlers = [
			request.HTTPHandler(),
			request.HTTPSHandler(context=self.ssl_verify)
		]
		self.cookie_file = "cookie.txt" ; self._cookiejar=None ; self.loadCookie()
		self._global_proxy_enable = False ; self.global_proxy_enable = self._global_proxy_enable

	@property
	def global_proxy_enable(self):
		return self._global_proxy_enable
		
	@global_proxy_enable.setter
	def global_proxy_enable(self,enable):
		""" 选择是否启用代理,self.global_proxy设置代理 """
		if isinstance(enable,bool):
			self._global_proxy_enable = enable
		else:
			raise TypeError("args 'enable' should be <bool> not <%s>"%(type(enable)))
		if enable == True:
			self.setHandler(request.ProxyHandler(self.global_proxy))
		elif enable == False:
			self.setHandler(request.ProxyHandler({}))

	def openUrl(self,url="",args={},method="GET",encoding=None,headers=None,timeout=None,proxy_list=[],handlers=None):
		"""
		url:		请求的地址,如使用GET可直接包含参数无需args
		args:		参数字典
		method:		请求方法[GET/POST]
		encoding:	用于对rul字符进行编码,不设置则使用self.default_encodeing
		headers,	请求头字典,不设置则使用self.headers
		timeout,	超时检测,若超时返回timeouterrorm,不设置则使用self.timeout
		proxy_list,	随机代理列表(未测试)
		handlers	自定义urllib.request.HTTPHandler()对象,不设置则使用self.handlers
		"""
		if encoding == None:
			encoding = self.default_encodeing

		if headers == None:
			headers = self.headers

		_request = None

		if method.upper()=="GET":
			_request = request.Request(
				url = "%s?%s"%(url,parse.urlencode(args,encoding=encoding)) if args!={} else url,
				headers = headers,
				origin_req_host = None,
				unverifiable = False,
				method = 'GET'
				)
		elif method.upper()=="POST":
			# sleep_time = random.randrange(4,5)
			# print(sleep_time,"s ....")
			# time.sleep(sleep_time)
			# post_log(url+str(args))
			_request = request.Request(
				url = url,
				data = bytes(parse.urlencode(args,encoding=encoding),encoding='UTF8') if isinstance(args,dict) else bytes(args,encoding="UTF8"),
				headers = headers,
				origin_req_host = None,
				unverifiable = False,
				method = 'POST'
				)

		proxy = None
		if proxy_list!=[]:
			proxy = random.choice(proxy_list)

		if handlers == None:
			handlers = self.handlers
		opener = request.build_opener(*handlers)
		if timeout == None:
			timeout = self.timeout
		_response = opener.open(_request,timeout=timeout)
		
		res = {
			"status":_response.status,
			"headers":{header[0]: header[1] for header in _response.getheaders()},
			"content":self.decodeHtml(_response.read(),encoding),
			"reason":_response.reason
		}
		return res
		
	def setHandler(self,handler):
		"""" 添加/修改本对象的handler """
		assert(isinstance(handler,request.BaseHandler))
		for h in self.handlers:
			if isinstance(h,type(handler)):
				self.handlers.remove(h)
		self.handlers.append(handler)

	def loadCookie(self,url="",headers=None):
		""" 
		从self.cookie_file加载filecookie对象,添加到self.handlers
		通过url,headers访问一个站点获得cookie
		"""
		_cookiejar = cookiejar.MozillaCookieJar(self.cookie_file)
		cookie_handler = request.HTTPCookieProcessor(_cookiejar)
		self.setHandler(cookie_handler)
		if url != "":
			self.openUrl(
				url = url,
				headers = headers,
				timeout = self.timeout
			)
		self._cookiejar = cookie_handler.cookiejar

	def saveCookie(self):
		"""
		保存cookie到self.cookie_file
		"""
		self._cookiejar.save(self.cookie_file)

	def gzipPage(self,data):
		"""
		对使用gzip压缩的数据进行解码
		data为response html原始字节
		返回解码后的字符字节
		"""
		buff = BytesIO(data) 
		res = gzip.GzipFile(fileobj=buff).read()
		return res

	def decodeHtml(self,data,encoding=None):
		"""
		data为response html原始字节
		对data用encoding解码
		自动对gzip格式进行处理
		返回解码后的字符
		"""
		if encoding == None:
			encoding = self.default_encodeing
		res = None
		if b'\x1f\x8b\x08\x00\x00\x00\x00' in data: # gzip
			res = self.gzipPage(data).decode(encoding)
		else:
			res = data.decode(encoding)
		return res

def post_log(s):
	time_tuple = time.localtime(time.time())
	time_str = ("{}月{}日{}点{}分{}秒".format(time_tuple[1],time_tuple[2],time_tuple[3],time_tuple[4],time_tuple[5]))
	with open("post_log.txt","a",encoding="UTF8") as f:
		f.write(s+"\t"+time_str+"\n")
