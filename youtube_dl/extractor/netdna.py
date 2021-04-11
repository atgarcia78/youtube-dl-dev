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

 
    @staticmethod
    def get_video_info(url):
        
        #NetDNAIE.to_screen(f"{text}:{url}")
        #_restr = r'(?:(Download)?[\ ]+|)(?P<title_url>[^\.]+)\.(?P<ext>[^\ ]+)[\ ]+\[(?P<size>[^\]]+)\]'
        #_restr = r'(?P<title_url>[^\.\ ]+)\.(?P<ext>[^\ ]+)[\ ]+\[(?P<size>[^\]]+)\]'
        # _restr = r"(?P<title_url>[^\.\ ]+)\.(?P<ext>[^\ ]+) +\[(?P<size>[^\]]+)\]"
        # _text = text.replace("\n","")
        # if (res:=re.search(_restr, _text)):
        #     _title, ext, size = res.group('title_url', 'ext', 'size')
        #     _title = _title.upper().replace("-", "_")
        #     _size = size.split(' ')
        #     _sizenumb = _size[0].replace(',','.')
        #     if _sizenumb.count('.') == 2:
        #         _sizenumb = _sizenumb.replace('.','', 1)
        #     _unit = _size[1].upper()
        # if len(_sizenumb.split('.')) == 2:
        #     if len((_temp:=_sizenumb.split('.')[1])) > 1:
        #         _temp = "0." + _temp
        #         _round = round(_temp,1)
        #         _sizenumb = int(_sizenumb[0])+
        # else: _sizenumb += '.0' 
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
            return({'id': videoid, 'title': title, 'name': f"{videoid}_{title}.{ext}", 'size': float(_num)*NetDNAIE._DICT_BYTES[_unit]})
        else:
            return({'id': None})


        

    
    def _get_filesize(self, url, cl):
        
        count = 0
        while (count<3):
            
            try:
                
                res = cl.head(url)
                if res.status_code > 400:
                    time.sleep(5)
                    count += 1
                else:    
                    return int_or_none(res.headers.get('content-length'))
        
            except (httpx.HTTPError, httpx.CloseError, httpx.RemoteProtocolError, httpx.ReadTimeout, 
                    httpx.ProxyError, AttributeError, RuntimeError) as e:
                count += 1
            
    
    def _real_extract(self, url):        
        
        title_url, ext_url = re.search(self._VALID_URL,url).group("title_url", "ext")
        self.report_extraction(title_url)
        
        #self.to_screen(f"{title_url} : lock {NetDNAIE._PROF_LOCK}")    
    
        #(prof_id, prof_ff) = self._get_ff_prof()
        prof_id = random.randint(0,5)
        prof_ff = FirefoxProfile(self._FF_PROF[prof_id])
        prof_ff.set_preference('network.proxy.type', 0)
        prof_ff.update_preferences()
 
        
        self.to_screen(f"{title_url} : ffprof [{prof_id}]")      
        
                        
                
        try:
            
            driver = None
            client = None
            opts = Options()
            opts.headless = True
            driver = Firefox(options=opts, firefox_profile=prof_ff)
            driver.install_addon("/Users/antoniotorres/projects/comic_getter/myaddon/web-ext-artifacts/myaddon-1.0.zip", temporary=True)
            #driver.maximize_window()
            #time.sleep(5)     
            client = httpx.Client()
            #self.to_screen("title: " + (_title:=driver.title))
            _title = driver.title
            driver.get(url)
            time.sleep(1)
            try:                           
                WebDriverWait(driver, 30).until(ec.url_contains("download"))
            except Exception as e:
                pass
            
            if "file not found" in (_title:=driver.title.lower()) or "error" in _title:
                self.to_screen(f"{title_url} Page not found - {url}")
                raise ExtractorError(f"Page not found - {url}")
            
            else:
                
                self.to_screen(_title)
                
                try:
                    
                    el_title = None
                    try:
                        el_title = WebDriverWait(driver, 30).until(ec.presence_of_element_located((By.CSS_SELECTOR, "h1.h2")))
                    except Exception as e:                        
                        pass
                    
                    if el_title:
                        title, _ext = el_title.text.upper().replace('-','_').split('.')
                        ext = _ext.lower()
                    else:
                        title = title_url.upper().replace('-', '_')
                        ext = ext_url
                    
                    size = re.findall(r'<strong>([^<]+)<', driver.find_element_by_css_selector("p.h4").get_attribute('innerHTML'))
                    _sizenumb = size[0].split(' ')[0].replace(',','.')
                    if _sizenumb.count('.') == 2:
                        _sizenumb = _sizenumb.replace('.','', 1)    
                    str_id = f"{title}{_sizenumb}" 
                    videoid = int(hashlib.sha256(str_id.encode('utf-8')).hexdigest(),16) % 10**8             
                
                    el_formats = [{'url' : el.get_attribute('href'), 'text': el.get_attribute('innerText')} 
                                    for el in driver.find_elements_by_css_selector("a.btn.btn--small")]
                    
                    
                    formats_video = []
                    
                    formats_video.append({'format_id': 'ORIGINAL', 
                                                'url': (_url:=driver.find_element_by_css_selector("a.btn.btn--xLarge").get_attribute('href')),
                                                'ext': ext,
                                                'filesize' : self._get_filesize(_url, client)
                                            })
                    
                    if el_formats and len(el_formats) > 1:                        
 
                        
                            for fmt in el_formats[1:]:
                                
                                driver.get(fmt['url'])
                                el_url = WebDriverWait(driver, 60).until(ec.presence_of_element_located((By.CSS_SELECTOR,"a.btn.btn--xLarge")))
                                formats_video.append({'format_id': fmt['text'], 
                                                'url': (_url:=el_url.get_attribute('href')),
                                                'ext': ext,
                                                'filesize' : self._get_filesize(_url, client)
                                               
                                            })
                                
                        
                    self._sort_formats(formats_video)
                    
                    entry = {
                        'id' : str(videoid),
                        'title': sanitize_filename(title,restricted=True),
                        'formats': formats_video,
                        'ext' : ext
                    }
                    
                    driver.quit()
                    client.close()
                    return(entry)
                    
        

                except Exception as e:
                    
                    raise
                
        except Exception as e:
            
            if driver:
                #driver.close()
                driver.quit()
            if client:
                client.close()
            raise ExtractorError(str(e))                 
            
            