from __future__ import unicode_literals

import json
import requests

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    std_headers
)


import re
import time

from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By

from pathlib import Path

from rclone import RClone

import logging

class OnlyFansBaseIE(InfoExtractor):

    _SITE_URL = "https://onlyfans.com/"
    

    _APP_TOKEN = "33d57ade8c02dbc5a333db99ff9ae26a"

    #log in via twitter
    _NETRC_MACHINE = 'twitter2'
    
    _USER_ID = "4090129"

       
    def __init__(self):
        
        self.app_token = self._APP_TOKEN
        self.session = requests.Session()
     
        self.twitter_xpath ="/html/body/div[1]/div[2]/div[1]/div/div/div[2]/form/a[1]"

        self.username_xpath = "/html/body/div[2]/div/form/fieldset[1]/div[1]/input"
        self.password_xpath = "/html/body/div[2]/div/form/fieldset[1]/div[2]/input"
        self.login_xpath = "/html/body/div[2]/div/form/fieldset[2]/input[1]"

        self.cookies = None
        self.user_agent = None         
        
        self.profile = "/Users/antoniotorres/Library/Application Support/Firefox/Profiles/0khfuzdw.selenium0"
        self.opts = Options()
        
        
        self._COOKIES_PATH = Path(Path.home(), "testing/cookies.json")
        
        
                        
        
    def _init_cookies_and_headers(self):
        try:
            if not self.cookies:
                if self._COOKIES_PATH.exists():
                    with open(self._COOKIES_PATH, "r") as f:
                        self.cookies = json.loads(f.read())                    
                else:
                    self.to_screen("No cookie info nor cookie file found. Let's log in")
                    self._login()
        
            self.to_screen(self.cookies)
            self.session.cookies.clear()
            
            for cookie in self.cookies:
                if "user-agent" in cookie.get('name'): 
                    self.user_agent = cookie.get('value')
                    std_headers['User-Agent'] = self.user_agent
                else:                    
                    self.session.cookies.set(name=cookie.get('name'), value=cookie.get('value'), 
                                             domain=cookie.get('domain'), path=cookie.get('path'))
                    
            self.to_screen(list(self.session.cookies))
            
            self.session.headers.update({
                "Accept":"application/json, text/plain, */*",
                "User-Agent": self.user_agent
                })
                                
        except Exception as e:
            self.to_screen(f"[init_cookies] Exception {e}")
            
        
           
    def _copy_cookies_gdrive(self):

        rc = RClone()
        res = rc.copy(self._COOKIES_PATH, "gdrive:Temp")
      
    
    def _login(self):

        username, password = self._get_login_info()
    
        if not username or not password:
            self.raise_login_required(
                'A valid %s account is needed to access this media.'
                % self._NETRC_MACHINE)

        self.report_login()

        try:
            self.driver = Firefox(options=self.opts, firefox_profile=self.profile)
            self.driver.maximize_window()
            time.sleep(5)            
            self.user_agent = self.driver.execute_script("return navigator.userAgent")
            self.driver.get(self._SITE_URL)
            wait = WebDriverWait(self.driver, 120)
            twitter_element = wait.until(ec.visibility_of_element_located(
                 (By.XPATH, self.twitter_xpath) ))
   
            twitter_element.click()          

            username_element = wait.until(ec.visibility_of_element_located(                
                (By.XPATH, self.username_xpath) ))
            username_element.send_keys(username)
            password_element = self.driver.find_element_by_xpath(self.password_xpath)
            password_element.send_keys(password)
            login_element = self.driver.find_element_by_xpath(self.login_xpath)
            login_element.click()
            wait.until(ec.title_contains("OnlyFans"))

            self.cookies = self.driver.get_cookies()
            self.cookies.append({"name": "user-agent", "value" : self.user_agent})
            
            with open(self._COOKIES_PATH, "w") as f:
                json.dump(self.cookies, f)
            
            self._copy_cookies_gdrive()

        except Exception as e:
            print(e)
            
        self.driver.close()
        self.driver.quit()    
         
           

    def _extract_from_json(self, data_post, acc=None):

        info_dict = []
        
        index = -1
        
        if data_post['media'][0]['type'] == 'video':
            index = 0
        else:
            if len(data_post['media']) > 1:
                for j, data in enumerate(data_post['media'][1:]):
                    if data['type'] == 'video':
                        index = j + 1
                        break
            
        if index != -1:
            if acc:
                account = acc
            else:
                account = data_post['author']['username']
            
            datevideo = data_post['postedAt'].split("T")[0]
            videoid = str(data_post['id'])


            formats = []
            
            try:

                filesize = None
                try:
                    filesize = int(self.session.request("HEAD", data_post['media'][index]['info']['source']['source']).headers['content-length'])
                except Exception as e:
                    pass
                formats.append({
                    'format_id': "http-mp4",
                    'url': data_post['media'][index]['info']['source']['source'],
                    'width': data_post['media'][index]['info']['source']['width'],
                    'height': data_post['media'][index]['info']['source']['height'],
                    'filesize': filesize,
                    'format_note' : "source original"
                })
            except Exception as e:
                    print(e)
                    print("No source video format")

            try:
                    
                if data_post['media'][index]['videoSources']['720']:
                    filesize = None
                    try:
                        filesize = int(self.session.request("HEAD",data_post['media'][index]['videoSources']['720']).headers['content-length'])
                    except Exception as e:
                        pass
                    formats.append({
                        'format_id': "http-mp4",
                        'url': data_post['media'][index]['videoSources']['720'],
                        'width': data_post['media'][index]['info']['source']['width'],
                        'height': data_post['media'][index]['info']['source']['height'],
                        'format_note' : "source 720",
                        'filesize': filesize,
                    })

            except Exception as e:
                    print(e)
                    print("No info for 720p format")

            try:
                if data_post['media'][index]['videoSources']['240']:
                    filesize = None
                    try:
                        filesize = int(self.session.request("HEAD",data_post['media'][index]['videoSources']['240']).headers['content-length'])
                    except Exception as e:
                        pass
                    formats.append({
                        'format_id': "http-mp4",
                        'url': data_post['media'][index]['videoSources']['240'],
                        'format_note' : "source 240",
                        'filesize': filesize,
                    })

            except Exception as e:
                print(e)
                print("No info for 240p format")
            
           # self._check_formats(formats, videoid)
            if formats:
                self._sort_formats(formats)
                #ponemos la fecha del video como id para facilitar filtros
                info_dict = {
                    "id" :  datevideo.replace("-", "") + "_" + str(videoid),
                    "title" :  "post_from_" + account,
                    "formats" : formats
                }

        return info_dict

class OnlyFansResetIE(OnlyFansBaseIE):
    IE_NAME = 'onlyfans:reset'
    IE_DESC = 'onlyfans:reset'
    _VALID_URL = r"onlyfans:reset"

    def _real_initialize(self):

        self.cookies = None
        self._login()
            

class OnlyFansPostIE(OnlyFansBaseIE):
    IE_NAME = 'onlyfans:post'
    IE_DESC = 'onlyfans:post'
    _VALID_URL =  r"(?:(onlyfans:post:(?P<post>.*?):(?P<account>[\da-zA-Z]+))|(https?://(?:www\.)?onlyfans.com/(?P<post2>[\d]+)/(?P<account2>[\da-zA-Z]+)))"

    def _real_initialize(self):
        self._init_cookies_and_headers()              

    def _real_extract(self, url):
 
        try:
            self.report_extraction(url) 

            (post1, post2, acc1, acc2) = re.search(self._VALID_URL, url).group("post", "post2", "account", "account2")
            post = post1 or post2
            account = acc1 or acc2

            self.to_screen("post:" + post + ":" + "account:" + account)
        
            self.session.headers["user-id"] = self._USER_ID
            self.session.headers["Referer"] = self._SITE_URL + post + "/" + account
            self.session.headers["Origin"] = self._SITE_URL
            self.session.headers["Access-Token"] = self.session.cookies.get('sess')

            #print(self.session.headers)
            #print(self.session.cookies)

            r = self.session.request("GET","https://onlyfans.com/api2/v2/posts/" + post + \
                "?skip_users_dups=1&app-token=" + self.app_token, timeout=60)

            #print(r.text)

            data_post = json.loads(r.text)
            
            self.to_screen(data_post)
            
            return self._extract_from_json(data_post)

        except Exception as e:
            print(e)

class OnlyFansPlaylistIE(OnlyFansBaseIE):
    IE_NAME = 'onlyfans:playlist'
    IE_DESC = 'onlyfans:playlist'
    _VALID_URL = r"(?:(onlyfans:account:(?P<account>[^:]+)(?:(:(?P<mode>(?:date|favs|tips)))?))|(https?://(?:www\.)?onlyfans.com/(?P<account2>\w+)(?:(/(?P<mode2>(?:date|favs|tips)))?)$))"
    _MODE_DICT = {"favs" : "favorites_count_desc", "tips" : "tips_summ_desc", "date" : "publish_date_desc", "latest10" : "publish_date_desc"}
           
   
    def _real_initialize(self):
        self._init_cookies_and_headers()               

    def _real_extract(self, url):
 
        try:
            self.report_extraction(url)
            (acc1, acc2, mode1, mode2) = re.search(self._VALID_URL, url).group("account", "account2", "mode", "mode2")
            account = acc1 or acc2
            mode = mode1 or mode2
            if not mode:
                mode = "latest10"

            
            r = self.session.request("GET","https://onlyfans.com/api2/v2/users/" + account + "?" + "app-token=" + self.app_token, timeout=60)

            data_user = json.loads(r.text)
            user_id = data_user['id']
            n_videos = int(data_user.get('videosCount'))
            
            self.session.cookies.set(name="wallLayout", value="list")

            self.session.headers["user-id"] = self._USER_ID
            self.session.headers["Referer"] = self._SITE_URL + "/" + account + "/videos"
            self.session.headers["Origin"] = self._SITE_URL
            self.session.headers["Access-Token"] = self.session.cookies.get('sess')
            
            data_videos = [] 
            
            if mode=="date":

                url_getvideos_base = "https://onlyfans.com/api2/v2/users/" + str(user_id) + "/posts/videos?limit=100&order=" + self._MODE_DICT.get("date") + "&skip_users=all&skip_users_dups=1&pinned=0&app-token=" + self.app_token
                url_getvideos = url_getvideos_base
                time3 = ""                          

                self.to_screen("Found " + str(n_videos))
                self.to_screen("Fetching video details for download")

                for i in range(0, (n_videos//100 + 1)):

                    r = self.session.request("GET", url_getvideos, timeout=60)
                    if r:
                        data_videos.extend(json.loads(r.text))
                        time3 = data_videos[-1]["postedAtPrecise"]
                        url_getvideos = url_getvideos_base + "&beforePublishTime=" + str(time3)  
                    else:
                        raise ExtractorError("No videos")
                        

            elif mode in ("favs", "tips", "latest10"):                

                url_getvideos = "https://onlyfans.com/api2/v2/users/" + str(user_id) + "/posts/videos?limit=10&order=" + self._MODE_DICT.get(mode) + "&skip_users=all&skip_users_dups=1&pinned=0&app-token=" + self.app_token
                r = self.session.request("GET", url_getvideos, timeout=60)
                if r:
                    data_videos.extend(json.loads(r.text))
                else:
                    raise ExtractorError("No videos")

            #entries = []

            # for post in data_videos:
            #     info = self._extract_from_json(post, account)
            #     if info:
            #         entries.append(info)          

            #ej https://onlyfans.com/78193186/mreyesmuriel
            
            entries = [ self.url_result(url=f"{self._SITE_URL}{post.get('id')}/{account}", ie='OnlyFansPost') for post in data_videos]
            
           
            # for post in data_videos:
            #     if post["responseType"] == "post":
            #         postid = post.get("id")
                

            return self.playlist_result(entries, "Onlyfans:" + account, "Onlyfans:" + account)

        except Exception as e:
            self.to_screen(e)