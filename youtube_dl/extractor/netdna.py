# coding: utf-8
from __future__ import unicode_literals

import re

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    HEADRequest,
    int_or_none,
    sanitize_filename,
    std_headers
)

import hashlib
from queue import Queue
import random


import shutil
from selenium.webdriver import Firefox
from selenium.webdriver import FirefoxProfile
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time
import httpx
import json
import threading


class NetDNAIE(InfoExtractor):
    IE_NAME = "netdna"
    _VALID_URL = r'https?://(www\.)?netdna-storage\.com/f/[^/]+/(?P<title_url>[^\.]+)\.(?P<ext>[^\.]+)\..*'
    _DICT_BYTES = {'KB': 1024, 'MB': 1024*1024, 'GB' : 1024*1024*1024}

    _FF_PROF = [        
            "/Users/antoniotorres/Library/Application Support/Firefox/Profiles/0khfuzdw.selenium0","/Users/antoniotorres/Library/Application Support/Firefox/Profiles/xxy6gx94.selenium","/Users/antoniotorres/Library/Application Support/Firefox/Profiles/wajv55x1.selenium2","/Users/antoniotorres/Library/Application Support/Firefox/Profiles/yhlzl1xp.selenium3","/Users/antoniotorres/Library/Application Support/Firefox/Profiles/7mt9y40a.selenium4","/Users/antoniotorres/Library/Application Support/Firefox/Profiles/cs2cluq5.selenium5_sin_proxy"
        ]
    
    _COUNT = 0
    _LOCK = threading.Lock()
    

 
    @staticmethod
    def get_video_info(url):
        
 
        title = None
        _num = None
        _unit = None
        client = None
        try:
            client = httpx.Client()
            res = client.get(url)

            if res.status_code < 400:
                _num_list = re.findall(r'File size: <strong>([^\ ]+)\ ([^\<]+)<',res.text)
                if _num_list:
                    _num = _num_list[0][0].replace(',','.')
                    if _num.count('.') == 2:
                        _num = _num.replace('.','', 1)
                    _unit = _num_list[0][1]
                _title_list = re.findall(r'h1 class="h2">([^\.]+).([^\<]+)<',res.text)
                if _title_list:
                    title = _title_list[0][0].upper().replace("-","_")
                    ext = _title_list[0][1].lower()
            
            client.close()
        except Exception as e:
            if client:
                client.close()        
       
        if title and _num and _unit:             
            str_id = f"{title}{_num}"
            videoid = int(hashlib.sha256(str_id.encode('utf-8')).hexdigest(),16) % 10**8
            return({'id': str(videoid), 'title': title, 'ext': ext, 'name': f"{videoid}_{title}.{ext}", 'size': float(_num)*NetDNAIE._DICT_BYTES[_unit]})
        else:
            return({'id': None})


    def wait_until(self, driver, time, method):
        
        error = False
        try:
            el = WebDriverWait(driver, time).until(method)
        except Exception as e:
            el = None
            error = True
        return({'error': error, 'el': el})   

    
    def _get_filesize(self, url):
        
        count = 0
        cl = httpx.Client()
        _res = None
        while (count<1):
            
            try:
                
                res = cl.head(url)
                if res.status_code > 400:
                    time.sleep(1)
                    count += 1
                else: 
                    _res = int_or_none(res.headers.get('content-length')) 
                    break
        
            except (httpx.HTTPError, httpx.CloseError, httpx.RemoteProtocolError, httpx.ReadTimeout, 
                    httpx.ProxyError, AttributeError, RuntimeError) as e:
                count += 1
        cl.close()
        return _res   
        
    
    def _real_extract(self, url):        
        
        #title_url, ext_url = re.search(self._VALID_URL,url).group("title_url", "ext")
        info_video = NetDNAIE.get_video_info(url)
        with NetDNAIE._LOCK:
            NetDNAIE._COUNT += 1
            pos = NetDNAIE._COUNT
        
        prof_id = pos%6 
        self.to_screen(f"New NetDNAIE instance, count instances [{pos}] profile firefox {prof_id}")
        prof_ff = FirefoxProfile(self._FF_PROF[prof_id])        
        opts = Options()
        opts.headless = True
        driver = Firefox(options=opts, firefox_profile=prof_ff)
        driver.maximize_window()
        time.sleep(1) 
        
        
        
        self.report_extraction(info_video.get('title'))
        
        self.to_screen(f"{info_video.get('title')} : ffprof [{prof_id}]")       

        
                        
                
        try:
            
           
            _title = driver.title
            driver.get(url)
            time.sleep(1)
            # try:                           
            #     WebDriverWait(driver, 60).until(ec.url_contains("download"))
            # except Exception as e:
            #     raise ExtractorError(f"Bypass didnt work till the last page - {url}")
            _reswait = self.wait_until(driver, 60, ec.url_contains("download"))
            if _reswait['error']:
                raise ExtractorError(f"Bypass didnt work till the last page - {url}")
                
            
            if "file not found" in (_title:=driver.title.lower()) or "error" in _title:
                self.to_screen(f"{info_video.get('title')} Page not found - {url}")
                raise ExtractorError(f"Page not found - {url}")
            
            else:
                
                self.to_screen(_title)
                
                try:
          
                    time.sleep(1)
                
                    
                    formats_video = []
                    #el_url = WebDriverWait(driver, 60).until(ec.presence_of_element_located((By.CSS_SELECTOR,"a.btn.btn--xLarge")))
                    _reswait = self.wait_until(driver, 60, ec.presence_of_element_located((By.CSS_SELECTOR,"a.btn.btn--xLarge")))
                    _filesize = None
                    if not _reswait['error']:
                        _url = _reswait['el'].get_attribute('href')
                        _filesize = self._get_filesize(_url)
                    if not _filesize:
                        driver.get(url)
                        # time.sleep(1)
                        # try:                           
                        #     WebDriverWait(driver, 60).until(ec.url_contains("download"))
                        # except Exception as e:
                        #     raise ExtractorError(f"Bypass didnt work till the last page - {url}")
                        _reswait = self.wait_until(driver, 60, ec.url_contains("download"))
                        if _reswait['error']:
                            raise ExtractorError(f"Bypass didnt work till the last page - {url}")

                        self.to_screen(driver.title)
                        time.sleep(1)
                        
                        # el_url = WebDriverWait(driver, 60).until(ec.presence_of_element_located((By.CSS_SELECTOR,"a.btn.btn--xLarge")))
                        # _url = el_url.get_attribute('href')
                        # _filesize = self._get_filesize(_url)
                        _reswait = self.wait_until(driver, 60, ec.presence_of_element_located((By.CSS_SELECTOR,"a.btn.btn--xLarge")))
                        _filesize = None
                        if not _reswait['error']:
                            _url = _reswait['el'].get_attribute('href')
                            _filesize = self._get_filesize(_url)
                        if not _filesize:
                            raise ExtractorError(f"error404 - {url}")
                    
                    formats_video.append({'format_id': 'ORIGINAL', 
                                                'url': _url,
                                                'ext': info_video.get('ext'),
                                                'filesize' : _filesize 
                                            })
                    
                    el_formats = [{'url' : el.get_attribute('href'), 'text': el.get_attribute('innerText')} 
                                    for el in driver.find_elements_by_css_selector("a.btn.btn--small")]
                    
                    if el_formats and len(el_formats) > 1:                        
 
                        
                            for fmt in el_formats[1:]:
                                
                                driver.get(fmt['url'])
                                el_url = WebDriverWait(driver, 60).until(ec.presence_of_element_located((By.CSS_SELECTOR,"a.btn.btn--xLarge")))
                                formats_video.append({'format_id': fmt['text'], 
                                                'url': (_url:=el_url.get_attribute('href')),
                                                'ext': info_video.get('ext'),
                                                'filesize' : self._get_filesize(_url)
                                               
                                            })
                                
                        
                    self._sort_formats(formats_video)
                    
                    entry = {
                        'id' : info_video.get('id'),
                        'title': sanitize_filename(info_video.get('title'),restricted=True),
                        'formats': formats_video,
                        'ext' : info_video.get('ext')
                    }
                    
                    driver.quit()
                    return(entry)
                    
        

                except Exception as e:
                    
                    raise
                
        except Exception as e:
            
            driver.quit() 

            
            if isinstance(e, ExtractorError):
                raise
            else:
                raise ExtractorError(str(e)) from e                
            
            