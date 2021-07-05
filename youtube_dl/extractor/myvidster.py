from __future__ import unicode_literals


import re
from tarfile import ExtractError
from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    int_or_none,
    std_headers,
    sanitize_filename
)
from collections import OrderedDict
import httpx
import html
import time
class MyVidsterBaseIE(InfoExtractor):

    _LOGIN_URL = "https://www.myvidster.com/user/"
    _SITE_URL = "https://www.myvidster.com"
    _NETRC_MACHINE = "myvidster"
    
    
    def _get_filesize(self, url):
        
        count = 0
        try:
            
            _res = None
            while (count<3):
                
                try:
                    
                    res = httpx.head(url, headers=std_headers)
                    if res.status_code > 400:
                        time.sleep(1)
                        count += 1
                    else: 
                        _res = int_or_none(res.headers.get('content-length')) 
                        break
            
                except Exception as e:
                    count += 1
        except Exception as e:
            pass

        
        return _res
    
    def _is_valid(self, url):
        
        res = httpx.head(url, headers=std_headers)
        return (res.status_code <= 200)
    
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
        
        _aux = {
                "Referer": self._LOGIN_URL,
                "Origin": self._SITE_URL,
                "Content-Type": "application/x-www-form-urlencoded"
        }
        _headers_post = self._headers_ordered(_aux)
        
        client.get(self._LOGIN_URL, headers=_headers)
        
        res = client.post(
                    self._LOGIN_URL,               
                    data=data,
                    headers=_headers_post,
                    timeout=60
                )

        if str(res.url) != "https://www.myvidster.com/user/home.php":
            raise ExtractorError("Login failed")


    def islogged(self, client):
        
        res = client.get(self._LOGIN_URL)
        return("action=log_out" in res.text)

class MyVidsterIE(MyVidsterBaseIE):
    IE_NAME = 'myvidster'
    _VALID_URL = r'https?://(?:www\.)?myvidster\.com/(?:video|vsearch)/(?P<id>\d+)/?(?:.*|$)'
    _NETRC_MACHINE = "myvidster"
    
    client = None

    def _real_initialize(self):
        self.client = httpx.Client()   
                       
        try:
            if not self.islogged(self.client): self._log_in(self.client)
        except Exception as e:
            self.client.close()

    def _real_extract(self, url):
        video_id = self._match_id(url)
        url = url.replace("vsearch", "video")
        _headers = self._headers_ordered({"Upgrade-Insecure-Requests": "1"}) 
        
        self.report_extraction(url)
        
        res = self.client.get(url, headers=_headers) 
        webpage = re.sub('[\t\n]', '', html.unescape(res.text))
        mobj = re.findall(r"<title>([^<]+)<", webpage)
        title = mobj[0] if mobj else url.split("/")[-1]    
        
        mobj = re.findall(r'rel=[\'\"]videolink[\'\"] href=[\'\"]([^\'\"]+)[\'\"]', webpage)
        videolink = httpx.URL(mobj[0]) if mobj and self._is_valid(mobj[0]) else ""
        
        
        mobj2 = re.findall(r"reload_video\([\'\"]([^\'\"]+)[\'\"]", webpage)
        embedlink = mobj2[0] if mobj2 and self._is_valid(mobj2[0]) else ""
        
        if videolink and embedlink:
            if (httpx.URL(videolink).host == httpx.URL(embedlink).host): real_url = videolink
            else: real_url = embedlink
        else:
            real_url = videolink or embedlink      
            
        if not real_url:
            raise ExtractError("Can't find real URL")

        #self.to_screen(f"{real_url}")   

        if real_url.startswith("https://www.myvidster.com/video"):
            
            res = self.client.get(real_url,headers=_headers)
            webpage = re.sub('[\t\n]', '', html.unescape(res.text))
            mobj = re.findall(r'source src="(?P<video_url>.*)" type="video', webpage)
            video_url = mobj[0] if mobj and self._is_valid(mobj[0]) else ""
            if not video_url: raise ExtractError("Can't find real URL")           
            filesize = self._get_filesize(video_url)


            format_video = {
                'format_id' : 'http-mp4',
                'url' : video_url,
                'filesize' : filesize,
                'ext' : 'mp4'
            }
            
            entry_video = {
                'id' : video_id,
                'title' : sanitize_filename(title, restricted=True),
                'formats' : [format_video],
                'ext': 'mp4'
            }
                
 


        else:

            entry_video = {
                '_type' : 'url_transparent',
                'url' : real_url,
                'id' : video_id,
                'title' : sanitize_filename(title, restricted=True)
            }

        return entry_video


class MyVidsterChannelPlaylistIE(MyVidsterBaseIE):
    IE_NAME = 'myvidster:channel:playlist'   
    _VALID_URL = r'https?://(?:www\.)?myvidster\.com/channel/(?P<id>\d+)/?(?P<title>\w+)?'
    _POST_URL = "https://www.myvidster.com/processor.php"
 
    client = None

    def _real_initialize(self):
        self.client = httpx.Client(headers=std_headers)   
                       
        try:
            if not self.islogged(): self._log_in(self.client)
        except Exception as e:
            self.client.close()



    def _real_extract(self, url):
        channelid = self._match_id(url)
        
        self.report_extraction(url)
        _headers = self._headers_ordered({"Upgrade-Insecure-Requests": "1"}) 
                
        res = self.client.get(url, headers=_headers)
        webpage = re.sub('[\t\n]', '', html.unescape(res.text))
        
        title = self._search_regex(r'<title>([\w\s]+)</title>', webpage, 'title', default=f"MyVidsterChannel_{channelid}", fatal=False)
        
        mobj = re.findall(r"display_channel\(.*,[\'\"](\d+)[\'\"]\)", webpage)
        num_videos = mobj[0] if mobj else 100000

        info = {
            'action' : 'display_channel',
            'channel_id': channelid,
            'page' : '1',
            'thumb_num' : num_videos,
            'count' : num_videos
        }
        
        _aux = {
                "Referer": url,                
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                "x-requested-with" : "XMLHttpRequest",
                "Accept": "*/*"
        }
        
        _headers_post = self._headers_ordered(_aux)
        
                
        res = self.client.post(
                    self._POST_URL,               
                    data=info,
                    headers=_headers_post,
                    
                )

        webpage = re.sub('[\t\n]', '', html.unescape(res.text))

        list_videos = re.findall(r'<a href=\"(/video/[^\"]+)\" class', webpage)

        entries = [self.url_result(f"{self._SITE_URL}{video}", "MyVidster") for video in list_videos]


        return {
            '_type': 'playlist',
            'id': channelid,
            'title': sanitize_filename(title, True),
            'entries': entries,
        }


