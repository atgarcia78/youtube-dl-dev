# coding: utf-8
from __future__ import unicode_literals

import re
import json


from .common import InfoExtractor

import requests 


from ..utils import (
    ExtractorError,
    get_element_by_attribute,  
    urljoin,
    int_or_none,
    sanitize_filename,
    std_headers

)

import random
import time
import threading

from selenium.webdriver import Firefox
from selenium.webdriver import FirefoxProfile
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By

import traceback
import sys

import httpx
class BoyFriendTVBaseIE(InfoExtractor):
    _LOGIN_URL = 'https://www.boyfriendtv.com/login/'
    _SITE_URL = 'https://www.boyfriendtv.com'
    _NETRC_MACHINE = 'boyfriendtv'
    _LOGOUT_URL = 'https://www.boyfriendtv.com/logout'
   
    
    _FF_PROF = [        
            "/Users/antoniotorres/Library/Application Support/Firefox/Profiles/0khfuzdw.selenium0","/Users/antoniotorres/Library/Application Support/Firefox/Profiles/xxy6gx94.selenium","/Users/antoniotorres/Library/Application Support/Firefox/Profiles/wajv55x1.selenium2","/Users/antoniotorres/Library/Application Support/Firefox/Profiles/yhlzl1xp.selenium3","/Users/antoniotorres/Library/Application Support/Firefox/Profiles/7mt9y40a.selenium4","/Users/antoniotorres/Library/Application Support/Firefox/Profiles/cs2cluq5.selenium5_sin_proxy", "/Users/antoniotorres/Library/Application Support/Firefox/Profiles/f7zfxja0.selenium_noproxy"
        ]
    
    def wait_until(self, driver, time, method):
        
        error = False
        try:
            el = WebDriverWait(driver, time).until(method)
        except Exception as e:
            el = None
            error = True
        return(el) 
    
    def wait_until_not(self, driver, time, method):
        
        error = False
        try:
            el = WebDriverWait(driver, time).until_not(method)
        except Exception as e:
            el = None
            error = True
        return(el)
    
    def _get_info_video(self, cl, url):
       
        count = 0
        while (count<5):
                
            try:
                
                res = cl.head(url)
                if res.status_code > 400:
                    
                    count += 1
                else: 
                    
                    _res = int_or_none(res.headers.get('content-length')) 
                    _url = str(res.url)
                    self.to_screen(f"{url}:{_url}:{_res}")
                    if _res and _url: 
                        break
                    else:
                        count += 1
        
            except Exception as e:
                count += 1
                
            time.sleep(1)
                
        if count < 5: return ({'url': _url, 'filesize': _res}) 
        else: return ({'error': 'max retries'})  
    
   

    
    def _login(self, driver):
        self.username, self.password = self._get_login_info()
        
        self.report_login()
        driver.get(self._LOGIN_URL)
        
        el_username = self.wait_until(driver, 60, ec.presence_of_element_located((By.CSS_SELECTOR, "input#login.form-control")))
        el_password = self.wait_until(driver, 60, ec.presence_of_element_located((By.CSS_SELECTOR, "input#password.form-control")))
        if el_username and el_password:
            el_username.send_keys(self.username)
            el_password.send_keys(self.password)
        el_login = driver.find_element_by_css_selector("input.btn.btn-submit")
        _current_url = driver.current_url
        el_login.click()
        self.wait_until(driver, 60, ec.url_changes(_current_url))
        


 
class BoyFriendTVIE(BoyFriendTVBaseIE):
    IE_NAME = 'boyfriendtv'
    _VALID_URL = r'https?://(?:(?P<prefix>m|www|es|ru|de)\.)?(?P<url>boyfriendtv\.com/videos/(?P<video_id>[0-9]+)/?(?:([0-9a-zA-z_-]+/?)|$))'

    _LOCK = threading.Lock()
    
    _COOKIES = None
    
    def _real_initialize(self):
        
        
        with BoyFriendTVIE._LOCK:
            if not BoyFriendTVIE._COOKIES:
                try:
        
                    prof_id = random.randint(0,5)         
                    self.to_screen(f"ffprof [{prof_id}]")
                    opts = Options()
                    opts.headless = True
                    prof_ff = FirefoxProfile(self._FF_PROF[prof_id]) 
                    driver = Firefox(options=opts, firefox_profile=prof_ff)
                    #driver.maximize_window()
                    time.sleep(5)
                    try:
                        driver.uninstall_addon('@VPNetworksLLC')
                    except Exception as e:            
                        self.to.screen(f"Error: {repr(e)}")
                        
                    driver.get(self._SITE_URL)
                    self.wait_until(driver, 60, ec.title_contains("Gay"))
                    driver.add_cookie({'name': 'rta_terms_accepted', 'value': 'true', 'domain': '.boyfriendtv.com', 'path': '/'})
                    driver.refresh()
                    self._login(driver)
                    
                    BoyFriendTVIE._COOKIES = driver.get_cookies()
                except Exception as e:
                    
                    raise ExtractorError("init issue")
                finally:
                    driver.quit()
                    

 
    
    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        _video_id = mobj.group('video_id')
        
        try:
            
            prof_id = random.randint(0,5)
            prof_ff = FirefoxProfile(self._FF_PROF[prof_id])
            opts = Options()
            opts.headless = True                        
            driver = Firefox(options=opts, firefox_profile=prof_ff)
            driver.maximize_window()
            time.sleep(5)            
            try:
                driver.uninstall_addon('@VPNetworksLLC')
            except Exception as e:
                lines = traceback.format_exception(*sys.exc_info())
                self._screen(f"Error: \n{'!!'.join(lines)}")       
            driver.get(self._SITE_URL)
            if (_cookies:=BoyFriendTVIE._COOKIES):
                driver.delete_all_cookies()
                for cookie in _cookies: driver.add_cookie(cookie)
            
            driver.refresh()
            driver.get(url)
            
            el_sources = self.wait_until(driver, 60, ec.presence_of_all_elements_located((By.CLASS_NAME, "download-item")))
            
            _cookies = driver.get_cookies()
            cl = httpx.Client() 
            for cookie in _cookies: cl.cookies.set(cookie['name'], cookie['value'], cookie['domain'], cookie['path'])
            cl.headers['user-agent'] = std_headers['User-Agent']
            
            _formats = []
            for _el in el_sources:
                _info_video = self._get_info_video(cl, _el.get_attribute('href'))
                _innertext = _el.get_attribute('innerText') 
                mobj = re.search(r'\n\t(?P<height>\d+)p', _innertext)
                _height = int(mobj.group('height')) if mobj else None
                _formats.append({
                    'url': _info_video.get('url'), 
                    'height':  _height,
                    'ext': 'mp4',
                    'filesize': _info_video.get('filesize'),
                    'format_id': f'http{_height}'})                   
           
            
            
            self._sort_formats(_formats)
            
            _title = self._search_regex((r'<h1>(?P<title>[^\<]+)\<', r'\"og:title\" content=\"(?P<title>[^\"]+)\"'), driver.page_source, "title", fatal=False, default="no_title", group="title")
            
                 
            
            
        except Exception as e:
            lines = traceback.format_exception(*sys.exc_info())
            self.to_screen(f"{repr(e)} {str(e)} \n{'!!'.join(lines)}")
            raise ExtractorError(e)
        finally:
            driver.quit()
            cl.close()
            
        return({
                'id': _video_id,
                'title': sanitize_filename(_title, restricted=True),
                'formats': _formats,
            
            })       


class BoyFriendTVPlayListIE(BoyFriendTVBaseIE):
    IE_NAME = 'boyfriendtvplaylist'
    IE_DESC = 'boyfriendtvplaylist'
    _VALID_URL = r'https?://(?:(m|www|es|ru|de)\.)boyfriendtv\.com/playlists/(?P<playlist_id>.*?)(?:(/|$))'

 
    
    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        playlist_id = mobj.group('playlist_id')


        try:
            
            prof_id = random.randint(0,5)         
            self.to_screen(f"ffprof [{prof_id}]")
            opts = Options()
            opts.headless = True
            prof_ff = FirefoxProfile(self._FF_PROF[prof_id]) 
            driver = Firefox(options=opts, firefox_profile=prof_ff)
            #driver.maximize_window()
            time.sleep(5)
            try:
                driver.uninstall_addon('@VPNetworksLLC')
            except Exception as e:            
                self.to.screen(f"Error: {repr(e)}")
                
            driver.get(self._SITE_URL)
            self.wait_until(driver, 60, ec.title_contains("Gay"))
            driver.add_cookie({'name': 'rta_terms_accepted', 'value': 'true', 'domain': '.boyfriendtv.com', 'path': '/'})
            driver.refresh()
        
            driver.get(url)

            el_sources = self.wait_until(driver, 60, ec.presence_of_all_elements_located((By.CSS_SELECTOR, "div.thumb.vidItem")))
            
            entries = [self.url_result((el_a:=el.find_element_by_tag_name('a')).get_attribute('href').rsplit("/", 1)[0], ie=BoyFriendTVIE.ie_key(), video_id=el.get_attribute('data-video-id'), video_title=sanitize_filename(el_a.get_attribute('title'), restricted=True)) for el in el_sources]

            
            el_title = driver.find_element_by_css_selector("h1")  
            
            _title = el_title.text.splitlines()[0]
            
        except Exception as e:
            lines = traceback.format_exception(*sys.exc_info())
            self.to_screen(f"{repr(e)} {str(e)} \n{'!!'.join(lines)}")
            raise ExtractorError(e)
        finally:
            driver.quit()

                

        return {
            '_type': 'playlist',
            'id': playlist_id,
            'title': sanitize_filename(_title, restricted=True),
            'entries': entries,
        }