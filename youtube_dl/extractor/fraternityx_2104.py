# coding: utf-8
from __future__ import unicode_literals

import json
import re
import random
import urllib.parse

from .common import InfoExtractor
from ..utils import (
    HEADRequest, multipart_encode,
    ExtractorError,
    clean_html,
    get_element_by_class,
    std_headers,
    get_elements_by_attribute,
    get_elements_by_class
)

import logging

class FraternityXBaseIE(InfoExtractor):
    _LOGIN_URL = "https://fraternityx.com/sign-in"
    _SITE_URL = "https://fraternityx.com"
    _LOG_OUT = "https://fraternityx.com/sign-out"
    _MULT_URL = "https://fraternityx.com/multiple-sessions"
    _ABORT_URL = "https://fraternityx.com/multiple-sessions/abort"
    _AUTH_URL = "https://fraternityx.com/authorize2"
    _NETRC_MACHINE = 'fraternityx'


        
 
    def initcfg(self):
        self.headers = dict()
        self.islogged()
        self._abort()
        self._login()
        self._logout()
        data = dict()
        data['headers'] = self.headers
        data['cookies'] = self._get_cookies(self._SITE_URL)
        return data

    def islogged(self):

        self._set_cookie('fraternityx.com', 'pp-accepted', 'true')
        webpage, _ = self._download_webpage_handle(
            self._SITE_URL,
            None,
            headers=self.headers
        )

        return ("Log Out" in webpage)
    
    def _abort(self):

        self.headers.update({
            "Referer": self._MULT_URL,
        })
        abort_page, url_handle = self._download_webpage_handle(
            self._ABORT_URL,
            None,
            "Log in ok after abort sessions",
            headers=self.headers
        )


    def _login(self):
        self.username, self.password = self._get_login_info()

        self.report_login()
        if not self.username or not self.password:
            self.raise_login_required(
                'A valid %s account is needed to access this media.'
                % self._NETRC_MACHINE)

        self._set_cookie('fraternityx.com', 'pp-accepted', 'true')

        self._download_webpage_handle(
            self._SITE_URL,
            None,
            'Downloading site page',
            headers=self.headers
        )
        self.headers.update({"Referer" : "https://fraternityx.com/episodes/1"})
        self._download_webpage_handle(
            self._LOGIN_URL,
            None,
            headers=self.headers
        )
        self.cookies = self._get_cookies(self._SITE_URL)
        #print(cookies)
        data = {
            "username": self.username,
            "password": self.password,
            "submit1" : "Log In",
            "_csrf-token": urllib.parse.unquote(self.cookies['X-EMA-CSRFToken'].coded_value)
            
        }
                   
        boundary = "-----------------------------" + str(random.randrange(111111111111111111111111111111, 999999999999999999999999999999))
        
        
        out, content = multipart_encode(data, boundary)        
        #print(out)
        #print(content)
        self.headers.update({
            "Referer": self._LOGIN_URL,
            "Origin": self._SITE_URL,
            "Content-Type": content,            
        })
        login_page, url_handle = self._download_webpage_handle(
            self._LOGIN_URL,
            None,
            'Login request',
            data=out,
            headers=self.headers
        )

        del self.headers["Content-Type"]
        del self.headers["Origin"]
        if self._AUTH_URL in url_handle.geturl():
            data = {
                "email": "a.tgarc@gmail.com",
                "last-name": "Torres",
                "_csrf-token": urllib.parse.unquote(self.cookies['X-EMA-CSRFToken'].coded_value)
            }
            out, content = multipart_encode(data, boundary)
            self.headers.update({
                "Referer": self._AUTH_URL,
                "Origin": self._SITE_URL,
                "Content-Type": content,               
            })
            auth_page, url_handle = self._download_webpage_handle(
                self._AUTH_URL,
                None,
                "Log in ok after auth2",
                data=out,
                headers=self.headers
            )
            del self.headers["Content-Type"]
            del self.headers["Origin"]

        
        if self._LOGIN_URL in url_handle.geturl():
            error = clean_html(get_element_by_class('login-error', login_page))
            if error:
                raise ExtractorError(
                    'Unable to login: %s' % error, expected=True)
            raise ExtractorError('Unable to log in')

        elif self._MULT_URL in url_handle.geturl():

            self._abort()



    def _log_out(self):
        self._request_webpage(
            self._LOG_OUT,
            None,
           'Log out'
       )

    def _extract_from_page(self, url):
        
        info_dict = []
        
        try:

            content, _ = self._download_webpage_handle(url, None, "Downloading video web page", headers=self.headers)
            #print(content)
            regex_title = r"<title>(?P<title>.*?)</title>"
            regex_emurl = r"iframe src=\"(?P<embedurl>.*?)\""
            embedurl = ""
            title = ""
            if re.search(regex_title, content):
                title = re.search(regex_title, content).group("title")
            if not title:
                title = url.rsplit("/", 1)[1].replace("-","_")
            else:
                title = title.split(" :: ")[0].replace(" ", "_")
                title = title.replace("/","_")
            if re.search(regex_emurl, content):
                embedurl = re.search(regex_emurl, content).group("embedurl")
            if not embedurl:
                raise ExtractorError("", cause="Can't find any video", expected=True)
            
            self.headers.update({'Referer' : url})
            content, _ = self._download_webpage_handle(embedurl, None, "Downloading embed video", headers=self.headers)
            #content = (webpage.read()).decode('utf-8')
            
            #print(content)
            if not self.username in content:
                raise ExtractorError("", cause="It seems you are not logged", expected=True)            
        
            regex_token = r"token: '(?P<tokenid>.*?)'"
            tokenid = ""
            tokenid = re.search(regex_token, content).group("tokenid")
            if not tokenid:
                raise ExtractorError("", cause="Can't find any token", expected=True)
                
            videourl = "https://videostreamingsolutions.net/api:ov-embed/parseToken?token=" + tokenid
            #print(videourl)

            self.headers.update({
                "Referer" : embedurl,
                "Accept" : "*/*",
                "X-Requested-With" : "XMLHttpRequest"})
            info = self._download_json(videourl, None, headers=self.headers)

            if not info:
                raise ExtractorError("", cause="Can't find any JSON info", expected=True)

            #print(info)
            videoid = str(info['xdo']['video']['id'])
            manifesturl = "https://videostreamingsolutions.net/api:ov-embed/manifest/" + info['xdo']['video']['manifest_id'] + "/manifest.m3u8"
            
            formats_m3u8 = self._extract_m3u8_formats(
                manifesturl, videoid, m3u8_id="hls", ext="mp4", entry_protocol='m3u8_native', fatal=False
            )

            if not formats_m3u8:
                raise ExtractorError("", cause="Can't find any M3U8 format", expected=True)

            self._sort_formats(formats_m3u8)
        
                        
            info_dict = {
                "id":str(info['xdo']['video']['id']),
                "title": title,
                "formats": formats_m3u8

            }
          
            return info_dict
        
        except ExtractorError as e:
            return({
                "id" : "error",
                "cause" : e.cause
            })



class FraternityXIE(FraternityXBaseIE):
    IE_NAME = 'fraternityx'
    IE_DESC = 'fraternityx'
    _VALID_URL = r'https?://(?:www\.)?fraternityx.com/episode/.*'    
    
    
    def _real_initialize(self):

        self.headers = dict()
        if not self.islogged():
            self._login()
        self.headers.update({            
            "Referer" : "https://fraternityx.com/episodes/1",
        })
        self.username, self.password = self._get_login_info() 

    def _real_extract(self, url):
        data = self._extract_from_page(url)
        #self._log_out()
        if not data:
            raise ExtractorError("Not any video format found")
        elif "error" in data['id']:
            raise ExtractorError(str(data['cause']))
        else:
            return(data)

class FraternityXPlayListIE(FraternityXBaseIE):
    IE_NAME = 'fraternityx:playlist'
    IE_DESC = 'fraternityx:playlist'
    _VALID_URL = r"https?://(?:www\.)?fraternityx\.com/episodes(?:$|/(?P<id>\d+))"
    _BASE_URL = "https://fraternityx.com"
    _BASE_URL_PL = "https://fraternityx.com/episodes/"

     
    def _real_initialize(self):
        self.headers = dict()
        if not self.islogged():
            self._login()
        self.headers.update({            
            "Referer" : "https://fraternityx.com/episodes/1",
        })
        self.username, self.password = self._get_login_info()

    def _real_extract(self, url):

        playlistid = re.search(self._VALID_URL, url).group("id")

        entries = []

        if not playlistid:
            
            playlistid = "All_FraternityX"

            i = 1
            while True:

                url_pl = f"{self._BASE_URL_PL}{i}"

                self.to_screen(url_pl)
            
                content, _ = self._download_webpage_handle(url_pl, playlistid, headers=self.headers)
                
            
                list_episodes = [f"{self._BASE_URL}{res[0]}" for el in get_elements_by_class("description", content) if (res:=re.findall(r'href="(.*)"', el)) != []]
                
                #print(list_episodes)
        
                for episode_url in list_episodes:
                    
                    entries.append(self.url_result(episode_url, ie=FraternityXIE.ie_key()))
                    
                #print(entries)

                if ">NEXT" in content:
                    
                    i += 1
                
                else:
                    break
        
        else:
            
            self.to_screen(url)
            content, _ = self._download_webpage_handle(url, playlistid, headers=self.headers)
            list_episodes = [f"{self._BASE_URL}{res[0]}" for el in get_elements_by_class("description", content) if (res:=re.findall(r'href="(.*)"', el)) != []]
                
            for episode_url in list_episodes:
                
                entries.append(self.url_result(episode_url, ie=FraternityXIE.ie_key()))    
            
        #self._log_out()
         
        return self.playlist_result(entries, f"fraternityx Episodes:{playlistid}", f"fraternityx Episodes:{playlistid}")