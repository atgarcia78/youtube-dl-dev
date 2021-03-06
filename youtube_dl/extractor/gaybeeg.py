# coding: utf-8
from __future__ import unicode_literals

import re
from sys import exc_info
import time
from youtube_dl.utils import ExtractorError

from .common import InfoExtractor

from concurrent.futures import (
    ThreadPoolExecutor,
    wait,
    ALL_COMPLETED
)

import traceback
import sys


import random
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver import FirefoxProfile
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver import FirefoxProfile



from queue import Queue

from .netdna import NetDNAIE

import logging

logger = logging.getLogger("gaybeeg")



class GayBeegBaseIE(InfoExtractor):
    
    _FF_PROF = [        
            "/Users/antoniotorres/Library/Application Support/Firefox/Profiles/0khfuzdw.selenium0","/Users/antoniotorres/Library/Application Support/Firefox/Profiles/xxy6gx94.selenium","/Users/antoniotorres/Library/Application Support/Firefox/Profiles/wajv55x1.selenium2","/Users/antoniotorres/Library/Application Support/Firefox/Profiles/yhlzl1xp.selenium3","/Users/antoniotorres/Library/Application Support/Firefox/Profiles/7mt9y40a.selenium4","/Users/antoniotorres/Library/Application Support/Firefox/Profiles/cs2cluq5.selenium5_sin_proxy", "/Users/antoniotorres/Library/Application Support/Firefox/Profiles/f7zfxja0.selenium_noproxy"
        ]
    
    
    
    def _get_entries_netdna(self, el_list):
        
        _list_urls_netdna = []
        for _el in el_list:
            for _el_tag in _el.find_elements_by_tag_name("a"):
                if "netdna-storage" in (_url:=_el_tag.get_attribute('href')):
                    _list_urls_netdna.append(_url)
        _final_list = list(set(_list_urls_netdna))
        
        logger.info(_final_list)
        
        entries = []
        
        for _item in _final_list:
            _info_video = NetDNAIE.get_video_info(_item)
            entries.append({'_type' : 'url', 'url' : _item, 'ie' : 'NetDNA', 'title': _info_video.get('title'), 'id' : _info_video.get('id'), 'filesize': _info_video.get('filesize')})
                
  
                                    
        return entries
    
   
    def _get_entries_gaybeeg(self, el_list):
        entries = [{'_type' : 'url', 'url' : _url, 'ie' : 'GayBeeg'}
                        for el in el_list
                                    for el_tagh2 in el.find_elements_by_tag_name("h2")
                                        for el_taga in el_tagh2.find_elements_by_tag_name("a")
                                            if "//gaybeeg.info" in (_url:=el_taga.get_attribute('href'))]    
        return entries
    
    def wait_until(self, driver, time, method):        
        
        try:
            el = WebDriverWait(driver, time).until(method)
        except Exception as e:
            el = None
    
        return(el)   

class GayBeegPlaylistPageIE(GayBeegBaseIE):
    IE_NAME = "gaybeeg:onepageplaylist"
    _VALID_URL = r'https?://(www\.)?gaybeeg\.info.*/page/.*'
    
        
    
    def _real_extract(self, url):        
        
        try:
            prof_id = random.randint(0,5)
            prof_ff = FirefoxProfile(GayBeegBaseIE._FF_PROF[prof_id])
            opts = Options()
            opts.headless = True             
            driver = None
            entries_final = None
            driver = Firefox(options=opts, firefox_profile=prof_ff)
            #driver.install_addon("/Users/antoniotorres/projects/comic_getter/myaddon/web-ext-artifacts/myaddon-1.0.zip", temporary=True)
            driver.maximize_window()
            time.sleep(5)
            try:
                driver.install_addon("/Users/antoniotorres/projects/comicdl/myaddon/web-ext-artifacts/myaddon-1.0.zip", temporary=True)
                driver.uninstall_addon('@VPNetworksLLC')
            except Exception as e:
                lines = traceback.format_exception(*sys.exc_info())
                self.to_screen(f"Error: \n{'!!'.join(lines)}")
            
            driver.refresh()
            self.to_screen(f"[worker_pl_main] init with ffprof[{prof_id}]")          
            self.report_extraction(url)
            driver.get(url)
            time.sleep(1)                
            #el_list = WebDriverWait(driver, 120).until(ec.presence_of_all_elements_located((By.XPATH, "//a[@href]")))
            el_list = WebDriverWait(driver, 120).until(ec.presence_of_all_elements_located((By.CLASS_NAME, "hentry-large")))
            #self.to_screen(f"{[el.text for el in el_list]}")
            if el_list:                
                entries_final = self._get_entries_netdna(el_list)         
            
            #driver.quit()   
            
        except Exception as e:
            self.to_screen(str(e))
            logger.error(str(e), exc_info=True)
            #if driver: 
            #    driver.quit()
        finally:
            driver.quit()        
        
        return {
            '_type': "playlist",
            'id': "gaybeeg",
            'title': "gaybeeg",
            'entries': entries_final
        } 
    
class GayBeegPlaylistIE(GayBeegBaseIE):
    IE_NAME = "gaybeeg:allpagesplaylist"    
    _VALID_URL = r'https?://(www\.)?gaybeeg\.info/(?:((?P<type>(?:site|pornstar|tag))(?:$|(/(?P<name>[^\/$\?]+)))(?:$|/$|/(?P<search1>\?(?:tag|s)=[^$]+)$))|((?P<search2>\?(?:tag|s)=[^$]+)$))'
    
        
    def _worker_pl(self, i):        
               
        prof_id = random.randint(0,5)
        prof_ff = FirefoxProfile(GayBeegBaseIE._FF_PROF[prof_id])  
        opts = Options()
        opts.headless = True
        self.to_screen(f"[worker_pl{i}] init with ffprof[{prof_id}]")
        
        try:
            driver = None
            driver = Firefox(options=opts, firefox_profile=prof_ff)
            #driver.install_addon("/Users/antoniotorres/projects/comic_getter/myaddon/web-ext-artifacts/myaddon-1.0.zip", temporary=True)
            driver.maximize_window()
            time.sleep(5)            
            try:
                driver.install_addon("/Users/antoniotorres/projects/comicdl/myaddon/web-ext-artifacts/myaddon-1.0.zip", temporary=True)
                driver.uninstall_addon('@VPNetworksLLC')
            except Exception as e:
                lines = traceback.format_exception(*sys.exc_info())
                self.to_screen(f"Error: \n{'!!'.join(lines)}")
            
            driver.refresh()
            
            
            while not self.queue_in.empty():
                info_dict = self.queue_in.get()
                url_p = info_dict['url']
                npage = info_dict['page']
                self.to_screen(f"[worker_pl{i}] page {npage}  {url_p}")
                if url_p == "KILL":
                    
                    self.completed += 1
                    self.to_screen(f"[worker_pl{i}] bye bye, completed {self.completed}")
                    #driver.close()
                    #driver.quit()                    
                    break
                elif url_p == "KILLANDCLEAN":
                    while(self.completed < self.workers - 1):
                        time.sleep(1)
                        self.to_screen(f"[worker_pl{i}] completed {self.completed}")
                    pending_pages = list(self.queue_nok.queue)
                    if pending_pages:
                        self.to_screen(f"[worker_pl{i}] retry with pending pages \n {pending_pages}")
                        for info_page in pending_pages:
                            self.queue_in.put(info_page)
                        self.queue_in.put({'url': "KILL", 'page': 0})
                        continue
                    else:
                        self.to_screen(f"[worker_pl{i}] no need to retry pending pages") 
                        #driver.close()
                        #driver.quit()
                        break
                        
                else:
                    try:
                        driver.get(url_p)
                        time.sleep(1)                

                        el_list = WebDriverWait(driver, 120).until(ec.presence_of_all_elements_located((By.CLASS_NAME, "hentry-large")))
                        if el_list:
                           
                            _entries = self._get_entries_netdna(el_list)
                            if _entries:
                                for entry in _entries:
                                    if entry.get('id'): self.queue_entries.put(entry)
                            self.to_screen(f"[worker_pl{i}]: entries [{len(_entries)}]\n {_entries}")

                        else:
                            self.queue_nok.put({'url': url_p, 'page': npage})
                    except Exception as e:
                        self.to_screen(f"[worker_pl{i}] {e}")
                        self.queue_nok.put({'url': url_p, 'page': npage})
                        
        except Exception as e:
            self.to_screen(f"[worker_pl{i}] {e}")
            logger.error(str(e), exc_info=True)
            #if driver:
                #driver.close()
                #driver.quit()
        finally:
            driver.quit()
        
            
                
    
    def _real_initialize(self):
  
        
        
        self.queue_in = Queue()
        self.queue_entries= Queue()
        self.queue_nok = Queue()
        
        
    
    def _real_extract(self, url):        
        
        try:
            prof_id = random.randint(0,5)
            prof_ff = FirefoxProfile(GayBeegBaseIE._FF_PROF[prof_id])
            opts = Options()
            opts.headless = True
            # opts.add_argument('--no-sandbox')
            # opts.add_argument('--ignore-certificate-errors-spki-list')
            # opts.add_argument('--ignore-ssl-errors')              
            driver = None
            entries_final = None
            driver = Firefox(options=opts, firefox_profile=prof_ff)
            #driver.install_addon("/Users/antoniotorres/projects/comic_getter/myaddon/web-ext-artifacts/myaddon-1.0.zip", temporary=True)
            driver.maximize_window()
            time.sleep(5)            
            try:
                driver.install_addon("/Users/antoniotorres/projects/comicdl/myaddon/web-ext-artifacts/myaddon-1.0.zip", temporary=True)
                driver.uninstall_addon('@VPNetworksLLC')
            except Exception as e:
                lines = traceback.format_exception(*sys.exc_info())
                self.to_screen(f"Error: \n{'!!'.join(lines)}")
            
            
            self.to_screen(f"[worker_pl_main] init with ffprof[{prof_id}]")
            
            driver.get("https://gaybeeg.info") 
            self.wait_until(driver, 30, ec.title_contains("GayBeeg"))
                        
            self.report_extraction(url)
            driver.get(url)
            time.sleep(1)                
            #el_list = WebDriverWait(driver, 120).until(ec.presence_of_all_elements_located((By.XPATH, "//a[@href]")))
            el_list = self.wait_until(driver, 120, ec.presence_of_all_elements_located((By.CLASS_NAME, "hentry-large")))
            #self.to_screen(f"{[el.text for el in el_list]}")
            if el_list:
                
                _entries = self._get_entries_netdna(el_list)
                if _entries:
                    logger.info(_entries)
                    for entry in _entries:
                        if entry.get('id'): self.queue_entries.put(entry)
            
            
            
            mobj = re.search(self._VALID_URL,url)
            
            _type, _name, _search1, _search2 = mobj.group('type','name','search1','search2')
            
            _search = _search1 or _search2
            
            
            _items_url_fix = [_item for _item in ["https://gaybeeg.info",_type,_name] if _item]
            
            _url_fix = "/".join(_items_url_fix)
            
            el_pagination = self.wait_until(driver, 30, ec.presence_of_all_elements_located((By.CLASS_NAME, "pagination")))
            
            if el_pagination:
                webpage = el_pagination[0].get_attribute("innerHTML")
                _n_pages = re.search(r'Page 1 of (?P<n_pages>[\d]+)<', webpage)
                if _n_pages:
                    n_pages = int(_n_pages.group("n_pages"))
                else:
                    n_pages = 0
                    #driver.quit()
                #driver.close()
                #driver.quit()

                    
                
                self.to_screen(f"[worker_pl_main] Playlist with {n_pages} pages including this main page. Starting to process the pending {n_pages - 1} pages")
                if n_pages == 2:
                    _items_url = [_item for _item in [_url_fix,"page","2", _search] if _item]
                    _url = "/".join(_items_url)                   
                    driver.get(_url)
                    time.sleep(1) 
                    el_list = self.wait_until(driver, 120, ec.presence_of_all_elements_located((By.CLASS_NAME, "hentry-large")))
                    #self.to_screen([el.text for el in el_list])
                    if el_list:
                        _entries = self._get_entries_netdna(el_list)
                        if _entries:
                            for entry in _entries:
                                if entry.get('id'): self.queue_entries.put(entry)
                        self.to_screen(f"[worker_pl_main]: entries [{len(_entries)}]\n {_entries}")
                    #driver.quit()
                elif n_pages > 2:    
                    #driver.quit()
                    for num in range(2,n_pages+1):
                        _items_url = [_item for _item in [_url_fix,"page",str(num), _search] if _item]
                        _url = "/".join(_items_url) 
                        
                                            
                        self.queue_in.put({'url': _url, 'page': num})
                                                
                    for _ in range(min(16,n_pages-1) - 1):
                        self.queue_in.put({'url': "KILL", 'page': 0})
                        
                    self.queue_in.put({'url': "KILLANDCLEAN", 'page': 0})
                        
                    self.to_screen(list(self.queue_in.queue))
                    
                    
                    self.workers = min(12,n_pages-1)
                    self.total = n_pages - 1
                    self.completed = 0
                    self.to_screen(f"[worker_pl_main] nworkers pool [{self.workers}] total pages to download [{self.total}]")
                    
                
                    with ThreadPoolExecutor(max_workers=self.workers) as ex:
                        for i in range(self.workers):
                            ex.submit(self._worker_pl,i) 
                        
                        #wait(futures,return_when=ALL_COMPLETED)

            # else:
                
            #     driver.quit()
                    
            entries_final = list(self.queue_entries.queue)   
            
        except Exception as e:
            self.to_screen(str(e))
            logger.error(str(e), exc_info=True)
            # if driver:
                
            #     driver.quit()
        finally:
            driver.quit()        
        
        return {
            '_type': "playlist",
            'id': "gaybeeg",
            'title': "gaybeeg",
            'entries': entries_final
        }       
        
        
class GayBeegIE(GayBeegBaseIE):
    IE_NAME = "gaybeeg:post"
    _VALID_URL = r'https?://(www\.)?gaybeeg\.info/\d\d\d\d/\d\d/\d\d/.*'
    

            
    def _real_extract(self, url):        
        
        try:
            entries = None
            prof_id = random.randint(0,5)
            opts = Options()
            opts.headless = True 
            # opts.add_argument('--no-sandbox')
            # opts.add_argument('--ignore-certificate-errors-spki-list')
            # opts.add_argument('--ignore-ssl-errors')  
            prof_ff = FirefoxProfile(GayBeegBaseIE._FF_PROF[prof_id])            
            driver = None            
            driver = Firefox(options=opts, firefox_profile=prof_ff)
            driver.maximize_window()
            time.sleep(5)   
            try:
                driver.install_addon("/Users/antoniotorres/projects/comicdl/myaddon/web-ext-artifacts/myaddon-1.0.zip", temporary=True)
                driver.uninstall_addon('@VPNetworksLLC')
            except Exception as e:
                lines = traceback.format_exception(*sys.exc_info())
                self.to_screen(f"Error: \n{'!!'.join(lines)}")
            
            driver.refresh()
            self.to_screen(f"[worker_pl_main] init with ffprof[{prof_id}]")
         
            self.report_extraction(url)
            driver.get(url)
            time.sleep(1)                
            #el_list = WebDriverWait(driver, 120).until(ec.presence_of_all_elements_located((By.XPATH, "//a[@href]")))
            el_list = WebDriverWait(driver, 120).until(ec.presence_of_all_elements_located((By.CLASS_NAME, "hentry-large")))
            
            if el_list:
                    entries = self._get_entries_netdna(el_list)
            #driver.quit()
            
        except Exception as e:
            logger.error(str(e), exc_info=True)
            # if driver:
            #     driver.quit()
        finally:
            driver.quit()
            
        if not entries:
                raise ExtractorError(f'no video info: {str(e)}')
        else:
            return{
            '_type': "playlist",
            'id': "gaybeeg",
            'title': "gaybeeg",
            'entries': entries
        }      
        
