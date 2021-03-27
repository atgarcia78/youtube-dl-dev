# coding: utf-8
from __future__ import unicode_literals

import re
import time

from .common import InfoExtractor
from ..utils import (
    ExtractorError,
    HEADRequest,
    int_or_none,
    sanitize_filename,
    std_headers
)

from concurrent.futures import (
    ThreadPoolExecutor,
    wait,
    ALL_COMPLETED
)




import shutil
import random
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver import FirefoxProfile
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By



from queue import Queue

from .netdna import NetDNAIE


class GayBeegIE(InfoExtractor):
    IE_NAME = "gaybeeg"
    _VALID_URL = r'https?://(www\.)?gaybeeg\.info/?.*'
    # _FF_PROF = [        
    #         FirefoxProfile("/Users/antoniotorres/Library/Application Support/Firefox/Profiles/0khfuzdw.selenium0"),
    #         FirefoxProfile("/Users/antoniotorres/Library/Application Support/Firefox/Profiles/xxy6gx94.selenium"),
    #         FirefoxProfile("/Users/antoniotorres/Library/Application Support/Firefox/Profiles/wajv55x1.selenium2"),
    #         FirefoxProfile("/Users/antoniotorres/Library/Application Support/Firefox/Profiles/yhlzl1xp.selenium3"),
    #         FirefoxProfile("/Users/antoniotorres/Library/Application Support/Firefox/Profiles/7mt9y40a.selenium4"),
    #         FirefoxProfile("/Users/antoniotorres/Library/Application Support/Firefox/Profiles/cs2cluq5.selenium5_sin_proxy")
    #     ]
    _FF_PROF = [        
            "/Users/antoniotorres/Library/Application Support/Firefox/Profiles/0khfuzdw.selenium0","/Users/antoniotorres/Library/Application Support/Firefox/Profiles/xxy6gx94.selenium","/Users/antoniotorres/Library/Application Support/Firefox/Profiles/wajv55x1.selenium2","/Users/antoniotorres/Library/Application Support/Firefox/Profiles/yhlzl1xp.selenium3","/Users/antoniotorres/Library/Application Support/Firefox/Profiles/7mt9y40a.selenium4","/Users/antoniotorres/Library/Application Support/Firefox/Profiles/cs2cluq5.selenium5_sin_proxy"
        ]
    
    def _worker_pl(self, i):
        
               
        prof_id = random.randint(0,5)
        prof_ff = self._FF_PROF[prof_id]
        self.to_screen(f"[worker_pl{i}] init with ffprof[{prof_id}]")
        
        try:
            driver = None
            driver = Firefox(options=self.opts, firefox_profile=prof_ff)
            driver.maximize_window()
            time.sleep(5)
            
            
            while not self.queue_in.empty():
                info_dict = self.queue_in.get()
                url_p = info_dict['url']
                npage = info_dict['page']
                self.to_screen(f"[worker_pl{i}] page {npage}  {url_p}")
                if url_p == "KILL":
                    
                    self.completed += 1
                    self.to_screen(f"[worker_pl{i}] bye bye, completed {self.completed}")
                    #driver.close()
                    driver.quit()                    
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
                        driver.quit()
                        break
                        
                else:
                    try:
                        driver.get(url_p)
                        time.sleep(1)                
                        el_list = WebDriverWait(driver, 120).until(ec.presence_of_all_elements_located((By.XPATH, "//a[@href]")))
                        if el_list:
                            entries = [self.url_result(el.get_attribute('href'), ie="NetDNA", video_title=(info_video:=NetDNAIE.get_video_info(el.get_attribute('text')))['title'], 
                                       video_id=info_video['videoid']) 
                                            for el in el_list
                                                if "dna-storage" in el.get_attribute('outerHTML')]
                            #entries = [self.url_result(el.get_attribute('href'), "NetDNA") for el in el_list if "dna-storage" in el.get_attribute('outerHTML')]
                            self.to_screen(f"[worker_pl{i}] entries for page_{npage} [{len(entries)}]\n {entries}")
                            for entry in entries:
                                self.queue_entries.put(entry)
                        else:
                            self.queue_nok.put({'url': url_p, 'page': npage})
                    except Exception as e:
                        self.to_screen(f"[worker_pl{i}] {e}")
                        self.queue_nok.put({'url': url_p, 'page': npage})
                        
        except Exception as e:
            self.to_screen(f"[worker_pl{i}] {e}")
            if driver:
                #driver.close()
                driver.quit()
        
            
                
    
    def _real_initialize(self):
        self.opts = Options()
        self.opts.headless = True     
        
        
        self.queue_in = Queue()
        self.queue_entries= Queue()
        self.queue_nok = Queue()
        
        # seed_json = self._download_json('https://www.passwordrandom.com/query?command=guid&format=json&count=1', None).get('char')[0]
        # self.to_screen(seed_json)
        
        # random.seed(seed_json)
        
    
    def _real_extract(self, url):        
        
        try:
            prof_id = random.randint(0,5)
            prof_ff = self._FF_PROF[prof_id]
            driver = None
            entries_final = None
            driver = Firefox(options=self.opts, firefox_profile=prof_ff)
            self.to_screen(f"[worker_pl_main] init with ffprof[{prof_id}]")
            driver.maximize_window()
            time.sleep(5)            
            self.report_extraction(url)
            driver.get(url)
            time.sleep(1)                
            el_list = WebDriverWait(driver, 120).until(ec.presence_of_all_elements_located((By.XPATH, "//a[@href]")))                    

            entries = [self.url_result(el.get_attribute('href'), ie="NetDNA", video_title=(info_video:=NetDNAIE.get_video_info(el.get_attribute('text')))['title'], 
                                       video_id=info_video['videoid']) 
                                            for el in el_list
                                                if "dna-storage" in el.get_attribute('outerHTML')]
            self.to_screen(f"[worker_pl_main] entries for main page [{len(entries)}]\n {entries}")
            for entry in entries:
                self.queue_entries.put(entry)
            
            el_pagination = driver.find_elements_by_class_name("pagination")
            
            if el_pagination:
                webpage = el_pagination[0].get_attribute("innerHTML")
                n_pages = int(re.search(r'Page 1 of (?P<n_pages>[\d]+)<', webpage).group("n_pages"))
                #driver.close()
                driver.quit()
                if not url.endswith("/"): url = f"{url}/"
                self.to_screen(f"[worker_pl_main] Playlist with {n_pages} pages including this main page. Starting thread pool for the pending {n_pages - 1} pages")
                
                for num in range(2,n_pages+1):                    
                    self.queue_in.put({'url': f"{url}page/{num}", 'page': num})
                    
                for _ in range(min(16,n_pages-1) - 1):
                    self.queue_in.put({'url': "KILL", 'page': 0})
                    
                self.queue_in.put({'url': "KILLANDCLEAN", 'page': 0})
                    
                self.to_screen(list(self.queue_in.queue))
                
                
                self.workers = min(16,n_pages-1)
                self.total = n_pages - 1
                self.completed = 0
                self.to_screen(f"[worker_pl_main] nworkers pool [{self.workers}] total pages to download [{self.total}]")
                with ThreadPoolExecutor(max_workers=self.workers) as ex:
                    for i in range(self.workers):
                        ex.submit(self._worker_pl,i) 
                    
                    #wait(futures,return_when=ALL_COMPLETED)

            else:
                #driver.close()
                driver.quit()
                    
            entries_final = list(self.queue_entries.queue)   
            
        except Exception as e:
            self.to_screen(str(e))
            if driver:
                #driver.close()
                driver.quit()        
        
        return {
            '_type': "playlist",
            'id': "gaybeeg",
            'title': "gaybeeg",
            'entries': entries_final
        }               


