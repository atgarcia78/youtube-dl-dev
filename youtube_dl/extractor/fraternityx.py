# coding: utf-8
from __future__ import unicode_literals


import re
import random


from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    sanitize_filename
)


import threading
import time
import traceback
import sys


from selenium.webdriver import Firefox
from selenium.webdriver import FirefoxProfile
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By



class FraternityXBaseIE(InfoExtractor):
    _LOGIN_URL = "https://fraternityx.com/sign-in"
    _SITE_URL = "https://fraternityx.com"
    _LOGOUT_URL = "https://fraternityx.com/sign-out"
    _MULT_URL = "https://fraternityx.com/multiple-sessions"
    _ABORT_URL = "https://fraternityx.com/multiple-sessions/abort"
    _AUTH_URL = "https://fraternityx.com/authorize2"
    _BASE_URL_PL = "https://fraternityx.com/episodes/"
    _NETRC_MACHINE = 'fraternityx'
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
        return({'error': error, 'el': el}) 
    
    def wait_until_not(self, driver, time, method):
        
        error = False
        try:
            el = WebDriverWait(driver, time).until_not(method)
        except Exception as e:
            el = None
            error = True
        return({'error': error, 'el': el})

    def _login(self, driver):
        self.username, self.password = self._get_login_info()

        
        if not self.username or not self.password:
            self.raise_login_required(
                'A valid %s account is needed to access this media.'
                % self._NETRC_MACHINE)
        
       
        _title = driver.title 
        
        #self.to_screen(_title)
        
        driver.get(self._SITE_URL)
        
        self.wait_until_not(driver, 60, ec.title_is(_title))
        
        _title = driver.title.upper()
        #self.to_screen(_title)
        if "WARNING" in _title:
            self.to_screen("Adult consent")
            el_enter = self.wait_until(driver, 30, ec.presence_of_element_located((By.CSS_SELECTOR, "a.enter-btn")))['el']
            if el_enter: el_enter.click()
        res = self.wait_until(driver, 30, ec.title_contains("Episodes"))
        
        el_top = self.wait_until(driver, 30, ec.presence_of_element_located((By.CSS_SELECTOR, "ul.inline-list")))['el']
        if "INSTANT ACCESS" in el_top.get_attribute('innerText').upper():
            self.report_login()
            driver.get(self._LOGIN_URL)
            el_username = self.wait_until(driver, 30, ec.presence_of_element_located((By.CSS_SELECTOR, "input#username")))['el']
            el_password = self.wait_until(driver, 30, ec.presence_of_element_located((By.CSS_SELECTOR, "input#password")))['el']
            el_username.send_keys(self.username)
            el_password.send_keys(self.password)
            el_login = driver.find_element_by_css_selector("button")
            _title = driver.title
            el_login.click()
            self.wait_until_not(driver, 30, ec.title_is(_title))
            _title = driver.title.upper()
            if "DENIED" in _title:
                self.to_screen("Abort existent session")
                el_abort = driver.find_element_by_css_selector("button")
                el_abort.click()
            res = self.wait_until(driver, 30, ec.title_contains("Episodes"))
            el_top = self.wait_until(driver, 30, ec.presence_of_element_located((By.CSS_SELECTOR, "ul.inline-list")))['el']
            if not "LOG OUT" in el_top.get_attribute('innerText').upper():
                raise ExtractorError("Login failed")
           
            
    def _logout(self, driver):
        driver.get(self._LOGOUT_URL)

    def _extract_from_page(self, driver, url):
        
        info_dict = []
        
        try:

            #content, _ = self._download_webpage_handle(url, None, "Downloading video web page", headers=self.headers)
            #print(content)
            driver.get(url)
            el_title = self.wait_until(driver, 30, ec.presence_of_element_located((By.CSS_SELECTOR, "title")))['el']
            _title = el_title.get_attribute("innerText")
            title = None
            if _title:
                title = _title.split(" :: ")[0].replace(" ", "_")
                self.to_screen(title)
            
            el_iframe = driver.find_element_by_tag_name("iframe")
            embedurl = el_iframe.get_attribute('src')
            #self.to_screen(f"embedurl:{embedurl}")
            driver.switch_to.frame(el_iframe)
            el_script = driver.find_element_by_css_selector("script")
            _data_str = el_script.get_attribute('innerText').replace(' ','').replace('\n','')
            #self.to_screen(_data_str)
            tokenid = re.findall(r"token:'([^']+)'", _data_str)[0] 
            #self.to_screen(f"tokenid:{tokenid}")          
 
                
            videourl = "https://videostreamingsolutions.net/api:ov-embed/parseToken?token=" + tokenid
            #self.to_screen(videourl)
            headers = dict()
            headers.update({
                "Referer" : embedurl,
                "Accept" : "*/*",
                "X-Requested-With" : "XMLHttpRequest"})
            info = self._download_json(videourl, None, headers=headers)
            #self.to_screen(info)
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
                "id": videoid,
                "title": title,
                "formats": formats_m3u8
            }
          
            return info_dict
        
        except ExtractorError as e:
            return({
                "id" : "error",
                "cause" : e.cause
            })
            
    
    def _extract_list(self, driver, playlistid, nextpages):
        
        
        _title = driver.title 
        

        
        driver.get(self._SITE_URL)
        
        self.wait_until_not(driver, 60, ec.title_is(_title))
        
        _title = driver.title.lower()
   
        if "warning" in _title:
            self.to_screen("Adult consent")
            el_enter = self.wait_until(driver, 30, ec.presence_of_element_located((By.CSS_SELECTOR, "a.enter-btn")))['el']
            if el_enter: el_enter.click()
        res = self.wait_until(driver, 30, ec.title_contains("Episodes"))
        
        entries = []

        i = 0

        while True:

            url_pl = f"{self._BASE_URL_PL}{int(playlistid) + i}"

            self.to_screen(url_pl)
            
            driver.get(url_pl)
            el_listmedia = self.wait_until(driver, 30, ec.presence_of_all_elements_located((By.CLASS_NAME, "description")))['el']
            for media in el_listmedia:
                el_tag = media.find_element_by_tag_name("a")
                el_title = el_tag.find_element_by_class_name("episode-tile") #class name weird but it is what its been used in site page
                _title = el_title.get_attribute('innerText').replace(" ", "_")
                _title = sanitize_filename(_title, restricted=True)
                entries.append(self.url_result(el_tag.get_attribute("href"), ie=FraternityXIE.ie_key(), video_title=_title))      

            _content = driver.page_source
            
            if not nextpages: break
            if "NEXT" in _content:
                i += 1
            else:
                break
            
        return entries
         
   
       



class FraternityXIE(FraternityXBaseIE):
    IE_NAME = 'fraternityx'
    IE_DESC = 'fraternityx'
    _VALID_URL = r'https?://(?:www\.)?fraternityx.com/episode/.*'
   
    
    _LOCK = threading.Lock()
    
    _COOKIES = None
    
    
    def _real_initialize(self):
       
        with FraternityXIE._LOCK:
            if not FraternityXIE._COOKIES:
                prof_id = random.randint(0,5)
                prof_ff = FirefoxProfile(self._FF_PROF[prof_id])
                opts = Options()
                opts.headless = True
         
                                
                driver = Firefox(options=opts, firefox_profile=prof_ff)
                driver.maximize_window()
                time.sleep(5)            
                try:
                    driver.install_addon("/Users/antoniotorres/projects/comicdl/myaddon/web-ext-artifacts/myaddon-1.0.zip", temporary=True)
                    driver.uninstall_addon('@VPNetworksLLC')
                except Exception as e:
                    lines = traceback.format_exception(*sys.exc_info())
                    self._screen(f"Error: \n{'!!'.join(lines)}")
                driver.delete_all_cookies()
                try:
                    self._login(driver)
                
                except Exception as e:
                    self.to_screen("error when login")
                    raise
                
                FraternityXIE._COOKIES = driver.get_cookies()
                driver.quit()
                #self.to_screen(FraternityXIE._COOKIES)
        

    def _real_extract(self, url):
        prof_id = random.randint(0,5)
        prof_ff = FirefoxProfile(self._FF_PROF[prof_id])
        opts = Options()
        opts.headless = True
           
                        
        driver = Firefox(options=opts, firefox_profile=prof_ff)  
        driver.maximize_window()
        time.sleep(5)            
        try:
            driver.install_addon("/Users/antoniotorres/projects/comicdl/myaddon/web-ext-artifacts/myaddon-1.0.zip", temporary=True)
            driver.uninstall_addon('@VPNetworksLLC')
        except Exception as e:
            lines = traceback.format_exception(*sys.exc_info())
            self._screen(f"Error: \n{'!!'.join(lines)}")       
        driver.get(self._SITE_URL)
        if (_cookies:=FraternityXIE._COOKIES):
            driver.delete_all_cookies()
            for cookie in _cookies:
                driver.add_cookie(cookie)
            
        driver.refresh()       
        data = self._extract_from_page(driver, url)    
        driver.quit()
        if not data:
            raise ExtractorError("Not any video format found")
        elif "error" in data['id']:
            raise ExtractorError(str(data['cause']))
        else:
            return(data)

class FraternityxOnePagePlayListIE(FraternityXBaseIE):
    IE_NAME = 'fraternityx:onepageplaylist'
    IE_DESC = 'fraternityx:onepageplaylist'
    _VALID_URL = r"https?://(?:www\.)?fraternityx\.com/episodes/(?P<id>\d+)"
   
 
    def _real_extract(self, url):

        playlistid = re.search(self._VALID_URL, url).group("id")
        prof_id = random.randint(0,5)
        prof_ff = FirefoxProfile(self._FF_PROF[prof_id])
        opts = Options()
        opts.headless = True
          
                        
        driver = Firefox(options=opts, firefox_profile=prof_ff)      
        driver.maximize_window()
        time.sleep(5)            
        try:
            driver.install_addon("/Users/antoniotorres/projects/comicdl/myaddon/web-ext-artifacts/myaddon-1.0.zip", temporary=True)
            driver.uninstall_addon('@VPNetworksLLC')
        except Exception as e:
            lines = traceback.format_exception(*sys.exc_info())
            self._screen(f"Error: \n{'!!'.join(lines)}")

        entries = self._extract_list(driver, playlistid, nextpages=False)  
        driver.quit()
        
        return self.playlist_result(entries, f"fraternityx:page_{playlistid}", f"fraternityx:page_{playlistid}")
    
class FraternityxAllPagesPlayListIE(FraternityXBaseIE):
    IE_NAME = 'fraternityx:allpagesplaylist'
    IE_DESC = 'fraternityx:allpagesplaylist'
    _VALID_URL = r"https?://(?:www\.)?fraternityx\.com/episodes/?$"
   
 
    def _real_extract(self, url):

        
        prof_id = random.randint(0,5)
        prof_ff = FirefoxProfile(self._FF_PROF[prof_id])
        opts = Options()
        opts.headless = True
             
                        
        driver = Firefox(options=opts, firefox_profile=prof_ff)        
        driver.maximize_window()
        time.sleep(5)            
        try:
            driver.install_addon("/Users/antoniotorres/projects/comicdl/myaddon/web-ext-artifacts/myaddon-1.0.zip", temporary=True)
            driver.uninstall_addon('@VPNetworksLLC')
        except Exception as e:
            lines = traceback.format_exception(*sys.exc_info())
            self._screen(f"Error: \n{'!!'.join(lines)}")

        entries = self._extract_list(driver, 1, nextpages=True)  
        driver.quit()
        
        return self.playlist_result(entries, f"fraternityx:AllPages", f"fraternityx:AllPages")


        

