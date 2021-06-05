from __future__ import unicode_literals


import re
from tarfile import ExtractError
from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    urlencode_postdata,
    HEADRequest,
    std_headers,
    sanitize_filename
)
from collections import OrderedDict
import httpx
import brotli
class MyVidsterBaseIE(InfoExtractor):

    _LOGIN_URL = "https://www.myvidster.com/user/"
    _SITE_URL = "https://www.myvidster.com"
    _NETRC_MACHINE = "myvidster"
    
    
    def _headers_ordered(self, extra=None):
        _headers = OrderedDict()
        
        if not extra: extra = dict()
        
        for key in ["User-Agent", "Accept", "Accept-Language", "Accept-Encoding", "Content-Type", "X-Requested-With", "Origin", "Connection", "Referer", "Upgrade-Insecure-Requests"]:
        
            value = extra.get(key) if extra.get(key) else std_headers.get(key)
            if value:
                _headers[key.lower()] = value
      
        
        return _headers

    def _log_in(self, client):
        
        username, password = self._get_login_info()
        self.to_screen(f"{username}:{password}")

        self.report_login()
        if not username or not password:
            self.raise_login_required(
                'A valid %s account is needed to access this media.'
                % self._NETRC_MACHINE)
        
               

        data = {
            "user_id": username,
            "password": password,
            "save_login" : "on",
            "submit" : "Log+In",
            "action" : "log_in"
        }

        _headers = self._headers_ordered({"Upgrade-Insecure-Requests": "1"})         
        _aux = dict()
        _aux.update({
                "Referer": self._LOGIN_URL,
                "Origin": self._SITE_URL,
                "Content-Type": "application/x-www-form-urlencoded"
            })
        _headers_post = self._headers_ordered(_aux)
        
        client.get(self._LOGIN_URL, headers=_headers)
        
        res = client.post(
                    self._LOGIN_URL,               
                    data=data,
                    headers=_headers_post,
                    timeout=60
                )

        if res.url != "https://www.myvidster.com/user/home.php":
            raise ExtractorError("Login failed")


    def islogged(self):
        
        webpage, _ = self._download_webpage_handle(self._LOGIN_URL, None)
        return("action=log_out" in webpage)

class MyVidsterIE(MyVidsterBaseIE):
    IE_NAME = 'myvidster'
    _VALID_URL = r'https?://(?:www\.)?myvidster\.com/(?:video|vsearch)/(?P<id>\d+)/?(?:.*|$)'
    _NETRC_MACHINE = "myvidster"
    
    client = None

    def _real_initialize(self):
        self.client = httpx.Client()   
                       
        self._log_in(self.client)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        url = url.replace("vsearch", "video")
        _headers = self._headers_ordered({"Upgrade-Insecure-Requests": "1"}) 
        res = self.client.get(url,headers=_headers)
        self.to_screen(f"{res.headers}:{res.request.headers}")
        if res.headers.get("content-encoding") == "br":
            webpage = (brotli.decompress(res.content)).decode("UTF-8")
        else: webpage = res.text

        res = re.findall(r"title>([^<]+)<", webpage)
       
        #self.to_screen(f"{webpage}")
        if res:
            title = res[0]
        else: title = url.split("/")[-1]

        title = sanitize_filename(title, restricted=True)
                
        real_url = None
        
        res = re.findall(r"onClick=\"reload_video\(\'([^\']*)\'", webpage.replace(" ",""))
        if res:
            real_url = res[0]
        else:
            res = re.findall(r'rel=\"videolink\"href\=\"([^\"]+)\"', webpage.replace(" ",""))
            if res:
                real_url = res[0]
            
        if not real_url:
            raise ExtractError("Can't find real URL")

        #self.to_screen(f"{real_url}")   

        if real_url.startswith("https://www.myvidster.com/video"):
            
            webpage = self._download_webpage(real_url, video_id)
            str_regex = r'source src="(?P<video_url>.*)" type="video'
            mobj = re.search(str_regex, webpage)

                        
            if mobj:
                video_url = mobj.group('video_url')

                std_headers['Referer'] = url
                std_headers['Accept'] = "*/*"
                reqhead = HEADRequest(video_url)
                res = self._request_webpage(reqhead, None, headers={'Range' : 'bytes=0-'})
                filesize = res.getheader('Content-Lenght')
                if filesize:
                    filesize = int(filesize)    

                format_video = {
                    'format_id' : 'http-mp4',
                    'url' : video_url,
                    'filesize' : filesize,
                    'ext' : 'mp4'
                }
            
                entry_video = {
                    'id' : video_id,
                    'title' : title,
                    'formats' : [format_video],
                    'ext': 'mp4'
                }
                
                return entry_video


        else:

            entry_video = {
                '_type' : 'url_transparent',
                'url' : real_url,
                'id' : video_id,
                'title' : title
            }

            return entry_video


class MyVidsterChannelIE(MyVidsterBaseIE):
    IE_NAME = 'myvidster:channel'
    #_VALID_URL = r'https?://(?:www\.)?myvidster\.com/channel/(?P<id>\d+)/?(?:.*|$)'
    _VALID_URL = r'https?://(?:www\.)?myvidster\.com/channel/(?P<id>\d+).*'
    _POST_URL = "https://www.myvidster.com/processor.php"
 

    def _real_initialize(self):
        if self.islogged():
            return
        else:
            self._log_in()

    def _real_initialize(self):
        if self.islogged():
            return
        else:
            self._log_in()

    def _real_extract(self, url):
        channelid = self._match_id(url)
        webpage = self._download_webpage(url, channelid, "Downloading main channel web page")
        title = self._search_regex(r'<title>([\w\s]+)</title>', webpage, 'title', default=f"MyVidsterChannel_{channelid}", fatal=False)
        
        num_videos = self._search_regex(r"display_channel\(.+,(\d+)\)", webpage, 'number of videos')

        info = {
            'action' : 'display_channel',
            'channel_id': channelid,
            'page' : 1,
            'thumb_num' : num_videos,
            'count' : num_videos
        }

        webpage, ulrh = self._download_webpage_handle(
            self._POST_URL,
            channelid,
            None,
            None,
            data=urlencode_postdata(info),
            headers={'Referer' : url, 'Accept' : '*/*', 'x-requested-with' : 'XMLHttpRequest', 'Content-type': 'application/x-www-form-urlencoded;charset=UTF-8'}
        )

        list_videos = re.findall(r'<a href=\"(/video/[^\"]+)\" class', webpage)

        entries = [self.url_result(f"{self._SITE_URL}{video}", "MyVidster") for video in list_videos]


        return {
            '_type': 'playlist',
            'id': channelid,
            'title': sanitize_filename(title, True),
            'entries': entries,
        }


