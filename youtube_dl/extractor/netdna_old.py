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
    _VALID_URL = r'https?://(www\.)?netdna-storage\.com/f/[^/]+/(?P<title_url>[^\.]+)\.(?:mp4|zip).*'
    _DICT_BYTES = {'KB': 1024, 'MB': 1024*1024, 'GB' : 1024*1024*1024}

    _FF_PROF = [        
            "/Users/antoniotorres/Library/Application Support/Firefox/Profiles/0khfuzdw.selenium0","/Users/antoniotorres/Library/Application Support/Firefox/Profiles/xxy6gx94.selenium","/Users/antoniotorres/Library/Application Support/Firefox/Profiles/wajv55x1.selenium2","/Users/antoniotorres/Library/Application Support/Firefox/Profiles/yhlzl1xp.selenium3","/Users/antoniotorres/Library/Application Support/Firefox/Profiles/7mt9y40a.selenium4","/Users/antoniotorres/Library/Application Support/Firefox/Profiles/cs2cluq5.selenium5_sin_proxy"
        ]

 
    @staticmethod
    def get_video_info(text, url):
        
        #NetDNAIE.to_screen(f"{text}:{url}")
        _restr = r'(?:(Download)?[\ ]+|)(?P<title_url>[^\.]+)\.(?P<ext>[^\ ]+)[\ ]+\[(?P<size>[^\]]+)\]'
        
        if (res:=re.search(_restr, text.replace('\n',' '))):
            title, ext, size = res.group('title_url', 'ext', 'size')
            title = title.upper().replace("-", "_")
            _size = size.split(' ')
            _sizenumb = _size[0].replace(',','.')
        # if len(_sizenumb.split('.')) == 2:
        #     if len((_temp:=_sizenumb.split('.')[1])) > 1:
        #         _temp = "0." + _temp
        #         _round = round(_temp,1)
        #         _sizenumb = int(_sizenumb[0])+
        # else: _sizenumb += '.0' 
            client = httpx.Client()
            res = client.get(url)
            if res.status_code == 200:
                _num_list = re.findall(r'File size: <strong>([^\ ]+)\ ',res.text)
                if _num_list:
                    _num = _num_list[0].replace(',','.')   
            else:
                _num = _sizenumb

            client.close()             
            str_id = f"{title}{_num}"
            videoid = int(hashlib.sha256(str_id.encode('utf-8')).hexdigest(),16) % 10**8
            return({'id': videoid, 'title': title, 'name': f"{videoid}_{title}.{ext}", 'size': float(_num)*NetDNAIE._DICT_BYTES[_size[1]]})
        else: return({'id': None})

    
    def _real_extract(self, url):        
        
        title_url = re.search(self._VALID_URL,url).group("title_url")
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
            WebDriverWait(driver, 60).until_not(ec.title_is(_title))
            
            if "File Not Found" in driver.title: 
                self.to_screen(f"{title_url} Page not found - {url}")
                raise ExtractorError(f"Page not found - {url}")
            
            else:
                try:
                    el1 = WebDriverWait(driver, 60).until(ec.presence_of_element_located((By.PARTIAL_LINK_TEXT, "DOWNLOAD")))                    
                except Exception as e:
                    pass
                
                try:
                    el11 = driver.find_elements_by_xpath("/html/body/section[1]/div[1]/header/h1")
                    el12 = driver.find_elements_by_xpath("/html/body/section/div[1]/header/p/strong")
                    if not el11:
                        el11 = driver.find_elements_by_xpath("/html/body/section[2]/div[1]/header/h1")
                    if not el12:
                        el12 = driver.find_elements_by_xpath("/html/body/section[2]/div[1]/header/p/strong")
                except Exception as e:
                    pass
                    
                title = el11[0].text.split('.')[0].upper().replace("-", "_")
                ext = el11[0].text.split('.')[1].lower()
                est_size_init = el12[0].text.split(' ')
                _sizenumb = est_size_init[0].replace(',','.')
                str_id = f"{title}{_sizenumb}"
                videoid = int(hashlib.sha256(str_id.encode('utf-8')).hexdigest(),16) % 10**8
                
                #self.to_screen(f"[redirect] {el1.get_attribute('href')}")
                driver.get(el1.get_attribute('href'))
                time.sleep(1)
                try:
                    el2 = WebDriverWait(driver, 60).until(ec.presence_of_element_located((By.PARTIAL_LINK_TEXT, "CONTINUE")))
                except Exception as e:
                    pass

                #self.to_screen(f"[redirect] {el2.get_attribute('href')}")
                driver.get(el2.get_attribute('href'))
                time.sleep(1)
                try:
                   # el3 = WebDriverWait(driver, 60).until(ec.element_to_be_clickable((By.ID,"btn-main")))
                   #self.to_screen(driver.title)
                   el3 = WebDriverWait(driver,60).until(ec.presence_of_element_located((By.ID, "x-token")))
                   el3.submit()
                except Exception as e:
                    pass
                #el3.click()
                time.sleep(1)               
                try:
                    #self.to_screen(driver.title)
                    el4 = WebDriverWait(driver, 60).until(ec.presence_of_element_located((By.ID, "x-token")))
                    _title = driver.title
                    el4.submit()                    
                except Exception as e:
                    pass

               
                
                time.sleep(1)
               
                WebDriverWait(driver, 60).until_not(ec.title_is(_title))
                #self.to_screen(f"title: {(_title:=driver.title.lower())}")
                if "error" in _title: 
                    self.to_screen(f"{title_url} Page not found - {url}")
                    raise ExtractorError(f"Page not found - {url}")
                try:
                    el5 = WebDriverWait(driver, 60).until(ec.presence_of_all_elements_located((By.XPATH, "//div[2]/a[@href]")))
                    
                except Exception as e:
                    self.to_screen(str(e))
                
                formats = [{'url': el.get_attribute('href'), 'text' : el.get_attribute('text').replace("\n", "").replace(" ","")} 
                           for el in el5
                           if el.get_attribute('href')]
                
                if formats:
                
                    self.to_screen(f"{title_url} : Extracting formats [{len(formats)}]")
                    if len(formats) > 1:                
                        
                        for i, f in enumerate(formats):
                            
                            driver.get(f['url'])
                            el = WebDriverWait(driver, 60).until(ec.presence_of_element_located((By.PARTIAL_LINK_TEXT, "DOWNLOAD")))
                            f['videourl'] = el.get_attribute('href')
                            el2 = driver.find_element_by_xpath("/html/body/section/div[1]/header/p/strong")
                            est_size = el2.text.split(' ')
                            f['estimated_size'] = float(est_size[0].replace(',',''))*self._DICT_BYTES[est_size[1]]
                            #self.to_screen(f"[format video page] {f['videourl']} Estimated size: {f['estimated_size']}")
                            try:
                                #ncount = 1
                                #filesize = None
                                #while (ncount > 0):
                                res = client.head(f['videourl'])
                                if res.status_code >= 400:
                                    time.sleep(5)
                                    driver.get(f['url'])
                                    el = WebDriverWait(driver, 60).until(ec.presence_of_element_located((By.PARTIAL_LINK_TEXT, "DOWNLOAD")))
                                    f['videourl'] = el.get_attribute('href')
                                    res = client.head(f['videourl'])
                                    if res.status_code >= 400:
                                        filesize = None
                                    else: filesize = res.headers.get('content-length', None)
                                else: filesize = res.headers.get('content-length', None)
                                    
                                    
                                #         ncount -= 1
                                #     else:
                                #filesize = res.headers.get('content-length', None)
                                if filesize: filesize = int(filesize)
                                    #  break                                
                            except Exception as e:
                                filesize = None
                            f['filesize'] = filesize
                            #self.to_screen(f"[format video page] {f['videourl']} Filesize: {f['filesize']}")
                            f['final_fsize'] = f['filesize'] or f['estimated_size']
                            videourl_short = f['videourl'].split('download')[0]
                            self.to_screen(f"{title_url} [format {i+1}/{len(formats)}] {f['text']} {videourl_short}... : Est {f['estimated_size']}B : Real {f['filesize']}B : Format {f['final_fsize']}B")
                            
                        formats_video = [{
                            'format_id' : f['text'],
                            'url' : f['videourl'],
                            'filesize' : f['final_fsize'],
                            'ext' : ext} for f in formats]
                        
            
                        self._sort_formats(formats_video)
                        
                    else:
                        try:
                            # ncount = 1
                            # filesize = None
                            # while (ncount > 0):
                            res = client.head(formats[0]['url'])
                            #    if res.status_code >= 400:
                                    #time.sleep(5)
                            #        ncount -= 1
                            #    else:
                            filesize = res.headers.get('content-length', None)
                            if filesize: filesize = int(filesize)
                            #        break           
                        except Exception as e:
                            filesize = None
                        estimated_size = float(est_size_init[0].replace(',',''))*self._DICT_BYTES[est_size_init[1]]
                        final_size = filesize or estimated_size
                        videourl_short = formats[0]['url'].split("download")[0]
                        self.to_screen(f"{title_url} [format video page] {formats[0]['text']} {videourl_short} Est {estimated_size}B : Real {filesize}B : Format {final_size}B")        
                        formats_video = [{
                            'format_id' : "download",
                            'url' : formats[0]['url'],
                            'filesize' : final_size,
                            'ext' : ext}]
                    
                    
                    
                    # with NetDNAIE._PROF_LOCK:
                    #     self.rel_ff_prof(prof_id)
                        
                    
                    entry = {
                        'id': str(videoid),
                        'title': sanitize_filename(title,restricted=True),
                        'formats': formats_video,
                        'ext': ext}

                    #driver.close()
                    driver.quit()
                    client.close()
                
                    return(entry)  
                                   
                else: 
                    el = driver.find_element_by_partial_link_text("DOWNLOAD")
                    videourl = el.get_attribute('href')
                    res = client.head(videourl)
                    if res.status_code >= 400:
                        time.sleep(5)
                        driver.get(videourl)
                        el = WebDriverWait(driver, 60).until(ec.presence_of_element_located((By.PARTIAL_LINK_TEXT, "DOWNLOAD")))
                        videourl = el.get_attribute('href')
                        res = client.head(videourl)
                        if res.status_code >= 400:
                            filesize = None
                        else: filesize = res.headers.get('content-length', None)
                    else: filesize = res.headers.get('content-length', None)
                    formats_video = [{
                        'format_id' : "download",
                        'url' : videourl,
                        'filesize' : filesize,
                        'ext' : ext}                   
                        
                    ]
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
            
            if driver:
                #driver.close()
                driver.quit()
            if client:
                client.close()
            raise ExtractorError(str(e))                 
            
            