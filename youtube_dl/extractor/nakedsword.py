# coding: utf-8

from __future__ import unicode_literals
from logging import info
from os import CLD_CONTINUED

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError, NO_DEFAULT, urlencode_postdata,
    sanitize_filename,
    std_headers
)



from threading import Lock

import httpx
import time
import json


from collections import OrderedDict

class NakedSwordBaseIE(InfoExtractor):
    IE_NAME = 'nakedsword'
    IE_DESC = 'nakedsword'
    
    _SITE_URL = "https://nakedsword.com/"
    _LOGIN_URL = "https://nakedsword.com/signin"
    _LOGOUT_URL = "https://nakedsword.com/signout"
    _NETRC_MACHINE = 'nakedsword'
    
    
    
   
    def _headers_ordered(self, extra=None):
        _headers = OrderedDict()
        
        if not extra: extra = dict()
        
        for key in ["User-Agent", "Accept", "Accept-Language", "Accept-Encoding", "Content-Type", "X-Requested-With", "Origin", "Connection", "Referer", "Upgrade-Insecure-Requests"]:
        
            value = extra.get(key) if extra.get(key) else std_headers.get(key)
            if value:
                _headers[key.lower()] = value
      
        
        return _headers
    
    def islogged(self):
        page, urlh = self._download_webpage_handle(
            self._SITE_URL,
            None
        )
        return ("/signout" in page)
    
    def _login(self, client:httpx.Client):
        
        self.report_login()
        username, password = self._get_login_info()
        if not username or not password:
            self.raise_login_required(
                'A valid %s account is needed to access this media.'
                % self._NETRC_MACHINE)            

        login_form = {
            "SignIn_login": username,
            "SignIn_password": password,
            "SignIn_returnUrl": "/",
            "SignIn_isPostBack": "true",
        }
        
        


        count = 0
        
        _headers = self._headers_ordered({"Upgrade-Insecure-Requests": "1"})         
        _aux = dict()
        _aux.update({"Referer": self._LOGIN_URL,"Origin": "https://nakedsword.com","Content-Type": "application/x-www-form-urlencoded", "Upgrade-Insecure-Requests": "1"})
        _headers_post = self._headers_ordered(_aux)
        while (count < 5):
        
            try:
                page = client.get(self._LOGIN_URL, headers=_headers)
                mobj = re.findall(r"\'SignIn_returnUrl\'value=\'([^\']+)\'", page.text.replace(" ",""))
                if mobj: login_form.update({"SignIn_returnUrl": mobj[0]})
                #self.to_screen(f"Count login: [{count}]")
                #self.to_screen(f"{page.request} - {page} - {page.request.headers} - {mobj}")
                time.sleep(2)            
                res = client.post(
                    self._LOGIN_URL,               
                    data=login_form,
                    headers=_headers_post,
                    timeout=60
                )
                #self.to_screen(f"{res.request} - {res} - {res.request.headers}")
                #self.to_screen("URL login: " + str(res.url))

                if str(res.url) != self._SITE_URL + "members":
                    count += 1
                else: break
            except Exception as e:
                self.to_screen(f"{type(e)}:{str(e)}")
                count += 1
                
        if count == 5:
            raise ExtractorError("unable to login")

    def _logout(self,client):
        
        _headers = self._headers_ordered()
        res = client.get(self._LOGOUT_URL, headers=_headers, timeout=120)
       


class NakedSwordSceneIE(NakedSwordBaseIE):
    IE_NAME = 'nakedsword:scene'
    _VALID_URL = r"https?://(?:www\.)?nakedsword.com/movies/(?P<movieid>[\d]+)/(?P<title>[^\/]+)/scene/(?P<id>[\d]+)/?$"

    _LOCK = Lock()
    _COOKIES = {}
    
    @staticmethod
    def _get_info(url):
        
        page = httpx.get(url)
        res = re.findall(r"class=\'MiMovieTitle\'[^\>]*\>([^\<]*)<[^\>]*>[^\w]+(Scene[^\<]*)\<",page.text)
        res2 = re.findall(r"\'SCENEID\'content\=\'([^\']+)\'", page.text.replace(" ",""))
        if res and res2:
            return({'id': res2[0], 'title': sanitize_filename(f'{res[0][0]}_{res[0][1].lower().replace(" ","_")}', restricted=True)})
   
    
    def _real_initialize(self):
        with NakedSwordSceneIE._LOCK:
            #self.to_screen(f"Init of NSwordScene extractor: {NakedSwordSceneIE._COOKIES}")
            if not NakedSwordSceneIE._COOKIES:
                try:
                                        
                    client = httpx.Client()
                    self._login(client)
                    NakedSwordSceneIE._COOKIES = client.cookies
                    
                except Exception as e:
                    raise
                finally:
                    client.close()
                
            


    def _real_extract(self, url):

        try:
            
            _headers = self._headers_ordered({"Upgrade-Insecure-Requests": "1"})
            client = httpx.Client()
        
            with NakedSwordSceneIE._LOCK:
                if not NakedSwordSceneIE._COOKIES:
                    try:
                        self._login(client)
                        NakedSwordSceneIE._COOKIES = client.cookies
                        client.cookies.set("ns_pfm", "True", "nakedsword.com")
                    except Exception as e:
                        raise
                else:
                    client.get(self._SITE_URL, headers=_headers)
                    auth = NakedSwordSceneIE._COOKIES.get("ns_auth")
                    if auth:
                        #self.to_screen(f"Load Cookie: [ns_auth] {auth}")
                        client.cookies.set("ns_auth", auth, "nakedsword.com")
                    client.cookies.set("ns_pfm", "True", "nakedsword.com")
                    
                    pk = NakedSwordSceneIE._COOKIES.get("ns_pk")
                    if pk:
                        #self.to_screen(f"Load Cookie: [ns_pk] {pk}")
                        self._set_cookie("nakedsword.com","ns_pk", pk)
        
        
            count = 5
            
            while (count > 0):
                
                try:
                    info_video = self._get_info(url)
                    if info_video: break
                    else: count -= 1
                except Exception as e:
                    count -= 1
                
            
                
         
            scene_id = None
            if info_video:
                scene_id = info_video.get('id')
                if scene_id:
                    stream_url_m3u8 = "https://nakedsword.com/scriptservices/getstream/scene/" + scene_id + "/HLS"
                    stream_url_dash = "https://nakedsword.com/scriptservices/getstream/scene/" + scene_id + "/DASH"
                else:
                    raise ExtractorError("Can't find sceneid")
            else:
                raise ExtractorError("Can't find sceneid")
        

            

            #self.to_screen(stream_url_m3u8)
            
            mpd_url_m3u8 = None
        
            count = 0
            
            _aux = dict()
            _aux.update({"Referer": url, "X-Requested-With": "XMLHttpRequest",  "Content-Type" : "application/json", "Accept": "application/json, text/javascript, */*; q=0.01"})
            _headers_json = self._headers_ordered(_aux)
        
            while (count < 5):
    
                try:
                    info_m3u8 = {}
                    #self.to_screen(f"Count m3u8 info: [{count+1}]")
                    client.get(url,headers=_headers)
                    time.sleep(2)                  
                    
                    res = client.get(stream_url_m3u8, headers=_headers_json, timeout=80)
                    
                    #self.to_screen(f"{res.request} - {res} - {res.request.headers} - {res.headers} - {res.content}")
                    
                    if res.content:
                        info_m3u8 = res.json()                                                   
                        if info_m3u8: break
                    
                        
                    #self.to_screen("No res")
                    count += 1
                            
                    
                              
                except Exception as e:
                    self.to_screen(f"{type(e)}: {str(e)}")
                    count += 1
                    continue


            if not info_m3u8:
                raise ExtractorError("Can't get json")    
            
        
            self.to_screen(info_m3u8)
            mpd_url_m3u8 = info_m3u8.get("StreamUrl")   
                
           
            if not mpd_url_m3u8: raise ExtractorError("Can't find mpd m3u8")    
            #self.to_screen(mpd_url_m3u8)     
            
            NakedSwordSceneIE._COOKIES = client.cookies
            
            
            formats_m3u8 = None
            _headers_m3u8 = self._headers_ordered({"Accept": "*/*", "Origin": "https://nakedsword.com", "Referer": self._SITE_URL})
                        
            count = 0
            while (count < 5):
        
                try:
                    time.sleep(2)
                    #self.to_screen(f"Count formats m3u8: [{count+1}]")
                    res = client.get(mpd_url_m3u8, headers=_headers_m3u8, timeout=60)
                    #self.to_screen(f"{res.request} - {res} - {res.headers} - {res.request.headers} - {res.content}")
                    m3u8_bytes = res.content
                    m3u8_doc = m3u8_bytes.decode(res.encoding, 'replace')
                    if m3u8_doc:                        
                        formats_m3u8 = self._parse_m3u8_formats(m3u8_doc, mpd_url_m3u8, ext="mp4", entry_protocol="m3u8_native", m3u8_id="hls")
                        break
                    else: count += 1
                    
                except Exception as e:
                    self.to_screen(f"{type(e)}: {str(e)}")
                    count += 1
                    continue

            if not formats_m3u8: raise ExtractorError("Can't get formats m3u8")
                
            n = len(formats_m3u8)
            for f in formats_m3u8:
                f['format_id'] = "hls-" + str(n-1)
                n = n - 1
                
            # info_dash = self._download_json(
            #         getstream_url_dash,
            #         scene_id,
            #     )

            # mpd_url_dash = info_dash.get("StreamUrl")


            # formats_dash = self._extract_mpd_formats(
            #     mpd_url_dash, scene_id, mpd_id="dash", fatal=False
            # )


                
            # n = len(formats_dash)
            # for f in formats_dash:
            #     f['format_id'] = "dash-" + str(n-1)
            #     n = n - 1
                
            

            # title = info_m3u8.get("Title", "nakedsword")
            # title = sanitize_filename(title, True)
            # title = title + "_scene_" + title_id

            #self._logout(client)
            
            #NakedSwordSceneIE._COOKIES = {}
            
            #formats = formats_m3u8 + formats_dash[:-5]
            formats = formats_m3u8
            
            self._sort_formats(formats)
            
            title = info_video.get('title')
        
        except Exception as e:
            raise ExtractorError(str(e))
        finally:
            client.close()

        return {
            "id": scene_id,
            "title": title,
            "formats": formats,
            "ext": "mp4"
        }

class NakedSwordMovieIE(NakedSwordBaseIE):
    IE_NAME = 'nakedsword:movie'
    _VALID_URL = r"https?://(?:www\.)?nakedsword.com/movies/(?P<id>[\d]+)/(?P<title>[a-zA-Z\d_-]+)/?$"
    _MOVIES_URL = "https://nakedsword.com/movies/"

 


    def _real_extract(self, url):

        mobj = re.match(self._VALID_URL, url)
        
        playlist_id = mobj.group('id')
        title = mobj.group('title')

        webpage = self._download_webpage(url, playlist_id, "Downloading web page playlist")

        #print(webpage)

        pl_title = self._html_search_regex(r'(?s)<title>(?P<title>.*?)<', webpage, 'title', group='title').split(" | ")[1]

        #print(title)

        scenes_paths = re.findall(rf'{title}/scene/([\d]+)', webpage)

        #print(scenes_paths)

        entries = []
        for scene in scenes_paths:
            _url = self._MOVIES_URL + playlist_id + "/" + title + "/" + "scene" + "/" + scene
            res = NakedSwordSceneIE._get_info(_url)
            if res:
                _id = res.get('id')
                _title = res.get('title')
            entry = self.url_result(_url, ie=NakedSwordSceneIE.ie_key(), video_id=_id, video_title=_title)
            entries.append(entry)

        #print(entries)

        

        return {
            '_type': 'playlist',
            'id': playlist_id,
            'title': sanitize_filename(pl_title, True),
            'entries': entries,
        }

class NakedSwordMostWatchedIE(NakedSwordBaseIE):
    IE_NAME = "nakedsword:mostwatched"
    _VALID_URL = r'https?://(?:www\.)?nakedsword.com/most-watched/?'
    _MOST_WATCHED = 'https://nakedsword.com/most-watched?content=Scenes&page='
    
    def _real_extract(self, url):      
       

        entries = []

        for i in range(1,5):
               
            webpage = self._download_webpage(f"{self._MOST_WATCHED}{i}", None, "Downloading web page playlist")
            if webpage:  
                #print(webpage)          
                videos_paths = re.findall(
                    r"<div class='SRMainTitleDurationLink'><a href='/([^\']+)'>",
                    webpage)     
                
                if videos_paths:

                    for j, video in enumerate(videos_paths):
                        _url = self._SITE_URL + video
                        res = NakedSwordSceneIE._get_info(_url)
                        if res:
                            _id = res.get('id')
                            _title = res.get('title')
                        entry = self.url_result(_url, ie=NakedSwordSceneIE.ie_key(), video_id=_id, video_title=_title)
                        entries.append(entry)
                else:
                    raise ExtractorError("No info")


                
            else:
                raise ExtractorError("No info")

                

        return {
            '_type': 'playlist',
            'id': "NakedSWord mostwatched",
            'title': "NakedSword mostwatched",
            'entries': entries,
        }


class NakedSwordStarsIE(NakedSwordBaseIE):
    IE_NAME = "nakedsword:stars"
    _VALID_URL = r'https?://(?:www\.)?nakedsword.com/(?P<typepl>(?:stars|studios))/(?P<id>[\d]+)/(?P<name>[a-zA-Z\d_-]+)/?$'
    _MOST_WATCHED = "?content=Scenes&sort=MostWatched&page="
    _NPAGES = {"stars" : 1, "studios" : 1}
    
    def _real_extract(self, url):      
       
        
        data_list = re.search(self._VALID_URL, url).group("typepl", "id", "name")
        
        entries = []

        for i in range(self._NPAGES[data_list[0]]):


            webpage = self._download_webpage(f"{url}{self._MOST_WATCHED}{i+1}", None, "Downloading web page playlist")
            if webpage:  
                #print(webpage)          
                videos_paths = re.findall(
                    r"<div class='SRMainTitleDurationLink'><a href='/([^\']+)'>",
                    webpage)     
                
                if videos_paths:

                    for j, video in enumerate(videos_paths):
                        
                        _url = self._SITE_URL + video
                        res = NakedSwordSceneIE._get_info(_url)
                        if res:
                            _id = res.get('id')
                            _title = res.get('title')                        
                        entry = self.url_result(_url, ie=NakedSwordSceneIE.ie_key(), video_id=_id, video_title=_title)
                        entries.append(entry)
                else:
                    raise ExtractorError("No info")

                if not "pagination-next" in webpage: break
                
            else:
                raise ExtractorError("No info")

                

        return {
            '_type': 'playlist',
            'id': data_list[1],
            'title':  f"NSw{data_list[0].capitalize()}_{''.join(w.capitalize() for w in data_list[2].split('-'))}",
            'entries': entries,
        }