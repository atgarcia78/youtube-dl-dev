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


import shutil
from selenium.webdriver import Firefox
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
    _VALID_URL = r'https?://(www\.)?netdna-storage\.com/f/[^/]+/(?P<title_url>[^\.]+)\.mp4.*'
    _DICT_BYTES = {'KB': 1024, 'MB': 1024*1024, 'GB' : 1024*1024*1024}
    _FFOX_PROFILES = "/Users/antoniotorres/testing/firefoxprofiles.json"
    _PROF_LOCK = threading.RLock()
    
 
    def get_ff_prof(self):
    
        with open(self._FFOX_PROFILES, "r") as f:
            ff_dict = json.loads(f.read())
            
        prof_path = None
        prof_id = None
        
        for prof in ff_dict['profiles']:
            if prof['count'] < 2:
                prof['count'] += 1
                prof_id = prof['id']
                prof_path = prof['path']                    
                break
        
        with open(self._FFOX_PROFILES, "w") as f:
            json.dump(ff_dict, f)
            
        return(prof_id, prof_path)
            
        
    
    def rel_ff_prof(self, prof_id):
        
            with open(self._FFOX_PROFILES, "r") as f:
                ff_dict = json.loads(f.read())
                
            for prof in ff_dict['profiles']:
                if prof['id'] == prof_id:
                    if prof['count'] > 0:
                        prof['count'] -= 1
                    break
                
            with open(self._FFOX_PROFILES, "w") as f:
                json.dump(ff_dict, f)
            
              
    
    def _real_extract(self, url):        
        
        title_url = re.search(self._VALID_URL,url).group("title_url")
        self.report_extraction(title_url)
        
        #self.to_screen(f"{title_url} : lock {NetDNAIE._PROF_LOCK}")
        
        with NetDNAIE._PROF_LOCK:
            count = 10
            while(count > 0):
                prof_id, prof_path = self.get_ff_prof()
                if not prof_id:
                    time.sleep(1)
                    count -= 1
                else: break
        
        self.to_screen(f"{title_url} : ffprof [{prof_id}]")
        
        opts = Options()
        opts.headless = True
        driver = Firefox(options=opts, firefox_profile=prof_path)
        driver.maximize_window()
        wait = WebDriverWait(driver, 15)        
        client = httpx.Client()
                        
                
        try:
        
            driver.get(url)
                       
            wait.until(ec.title_contains(""))
            
            if "File Not Found" in driver.title: 
                self.to_screen(f"{title_url} Page not found - {url}")
                raise ExtractorError(f"Page not found - {url}")
            
            else:
                try:
                    el1 = wait.until(ec.presence_of_element_located((By.LINK_TEXT, "DOWNLOAD")))                    
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
                    
                title = el11[0].text.split('.')[0].replace("-", "_")
                ext = el11[0].text.split('.')[1].lower()
                est_size_init = el12[0].text.split(' ')
                str_id = f"{title}{est_size_init[0]}"
                videoid = int(hashlib.sha256(str_id.encode('utf-8')).hexdigest(),16) % 10**8
                
                #self.to_screen(f"[redirect] {el1.get_attribute('href')}")
                driver.get(el1.get_attribute('href'))
                time.sleep(1)
                try:
                    el2 = wait.until(ec.presence_of_element_located((By.LINK_TEXT, "CONTINUE")))
                except Exception as e:
                    pass

                #self.to_screen(f"[redirect] {el2.get_attribute('href')}")
                driver.get(el2.get_attribute('href'))
                time.sleep(5)
                try:
                    el3 = wait.until(ec.element_to_be_clickable((By.ID,"btn-main")))
                except Exception as e:
                    pass
                el3.click()
                time.sleep(5)
                try:
                    el4 = wait.until(ec.element_to_be_clickable((By.ID, "btn-main")))
                except Exception as e:
                    pass

                el4.click()
                time.sleep(1)
                
                try:
                    el5 = wait.until(ec.presence_of_all_elements_located((By.XPATH, "//div[2]/a[@href]")))
                    
                except Exception as e:
                    pass
                
                formats = [{'url': el.get_attribute('href'), 'text' : el.get_attribute('text').replace("\n", "").replace(" ","")} 
                           for el in el5
                           if el.get_attribute('href')]
                
                self.to_screen(f"{title_url} : Extracting formats [{len(formats)}]")
                if len(formats) > 1:                
                    
                    for i, f in enumerate(formats):
                        
                        driver.get(f['url'])
                        el = wait.until(ec.presence_of_element_located((By.LINK_TEXT, "DOWNLOAD")))
                        f['videourl'] = el.get_attribute('href')
                        el2 = driver.find_element_by_xpath("/html/body/section/div[1]/header/p/strong")
                        est_size = el2.text.split(' ')
                        f['estimated_size'] = float(est_size[0].replace(',',''))*self._DICT_BYTES[est_size[1]]
                        #self.to_screen(f"[format video page] {f['videourl']} Estimated size: {f['estimated_size']}")
                        try:
                            ncount = 1
                            filesize = None
                            while (ncount > 0):
                                res = client.head(f['videourl'])
                                if res.status_code >= 400:
                                    #time.sleep(5)
                                    ncount -= 1
                                else:
                                    filesize = int(res.headers.get('content-length', None))
                                    break                                
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
                        ncount = 1
                        filesize = None
                        while (ncount > 0):
                            res = client.head(formats[0]['url'])
                            if res.status_code >= 400:
                                #time.sleep(5)
                                ncount -= 1
                            else:
                                filesize = int(res.headers.get('content-length', None))
                                break           
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
                
                driver.close()
                driver.quit()
                client.close()
                
                with NetDNAIE._PROF_LOCK:
                    self.rel_ff_prof(prof_id)
                    
                
                entry = {
                    'id': str(videoid),
                    'title': sanitize_filename(title,restricted=True),
                    'formats': formats_video,
                    'ext': ext}
            
                return(entry)                     
            
        except ExtractorError:
            raise
        except Exception as e:
            raise ExtractorError(e)                 
            
            