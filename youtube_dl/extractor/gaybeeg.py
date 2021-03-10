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
    wait as wait_ex,
    ALL_COMPLETED
)




import shutil
from selenium.webdriver import Firefox
from selenium.webdriver.firefox.options import Options
from selenium.webdriver import FirefoxProfile
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By

from queue import Queue


class GayBeegIE(InfoExtractor):
    IE_NAME = "gaybeeg"
    _VALID_URL = r'https?://(www\.)?gaybeeg\.info/?.*'
    

                
    def _worker_pl(self, i):
        
        self.to_screen(f"[worker_pl{i}] init")
        driver = Firefox(options=self.opts, firefox_profile=self.profiles_firefox[i])
        driver.maximize_window()
        time.sleep(5)
        waitd = WebDriverWait(driver, 120)
        
        while not self.queue_in.empty():
            url_p, npage = self.queue_in.get()
            self.to_screen(f"[worker_pl{i}] page {npage}  {url_p}")
            if url_p == "KILL":
                try:
                    driver.close()
                    driver.quit()
                except Exception as e:
                    pass
                break
            elif url_p == "KILLANDCLEAN":
                pending_pages = list(self.queue_nok.queue)
                self.to_screen(f"[worker_pl{i}] retry with pending pages \n {pending_pages}")
                for info_page in pending_pages:
                    self.queue_in.put(info_page)
            else:
                try:
                    driver.get(url_p)                
                    el_list = waitd.until(ec.presence_of_all_elements_located((By.XPATH, "//a[@href]")))
                    if el_list:
                        entries = [self.url_result(el.get_attribute('href'), "NetDNA") for el in el_list if "dna-storage" in el.get_attribute('outerHTML')]
                        self.to_screen(f"[worker_pl{i}] entries for page {npage} {url_p}\n {entries}")
                        for entry in entries:
                            self.queue_entries.put(entry)
                    else:
                        self.queue_nok.put(url_p, npage)
                except Exception as e:
                    self.to_screen(f"[worker_pl{i}] {e}")
                    self.queue_nok.put(url_p, npage)
                
    
    def _real_extract(self, url):
        

        self.opts = Options()
        self.opts.headless = True
        self.profiles_firefox = [        
            FirefoxProfile("/Users/antoniotorres/Library/Application Support/Firefox/Profiles/0khfuzdw.selenium0"),
            FirefoxProfile("/Users/antoniotorres/Library/Application Support/Firefox/Profiles/xxy6gx94.selenium"),
            FirefoxProfile("/Users/antoniotorres/Library/Application Support/Firefox/Profiles/wajv55x1.selenium2"),
            FirefoxProfile("/Users/antoniotorres/Library/Application Support/Firefox/Profiles/yhlzl1xp.selenium3"),
            FirefoxProfile("/Users/antoniotorres/Library/Application Support/Firefox/Profiles/7mt9y40a.selenium4"),
            FirefoxProfile("/Users/antoniotorres/Library/Application Support/Firefox/Profiles/cs2cluq5.selenium5_sin_proxy")
        ]
       
        driver = Firefox(options=self.opts, firefox_profile=self.profiles_firefox[0])
        driver.maximize_window()
        time.sleep(5)
        waitd = WebDriverWait(driver, 120)
        
        self.queue_in = Queue()
        self.queue_entries= Queue()
        self.queue_nok = Queue()
        
        try:
        
            self.report_extraction(url)
            driver.get(url)                
            el_list = waitd.until(ec.presence_of_all_elements_located((By.XPATH, "//a[@href]")))                    

            entries = [self.url_result(el.get_attribute('href'), "NetDNA") for el in el_list if "dna-storage" in el.get_attribute('outerHTML')]
            self.to_screen(f"[worker_pl_main] entries for main page\n {entries}")
            for entry in entries:
                self.queue_entries.put(entry)
            
            el_pagination = driver.find_elements_by_class_name("pagination")
            
            if el_pagination:
                webpage = el_pagination[0].get_attribute("innerHTML")
                n_pages = int(re.search(r'Page 1 of (?P<n_pages>[\d]+)<', webpage).group("n_pages"))
                driver.close()
                driver.quit()
                if not url.endswith("/"): url = f"{url}/"
                self.to_screen(f"[worker_pl_main] Playlist with {n_pages} pages including this main page. Starting thread pool for the pending {n_pages - 1} pages")
                
                for num in range(2,n_pages+1):                    
                    self.queue_in.put((f"{url}page/{num}", num))
                    
                for _ in range(5):
                    self.queue_in.put("KILL", 0)
                    
                self.queue_in.put("KILLANDCLEAN", 0)
                    
                self.to_screen(list(self.queue_in.queue))
                
                with ThreadPoolExecutor(max_workers=6) as ex:
                    futures = [ex.submit(self._worker_pl,i) for i in range(6)]
                    
                    done, pending = wait_ex(futures,return_when=ALL_COMPLETED)

                 
                entries_final = list(self.queue_entries.queue)   
            
        except Exception as e:
            self.to_screen(str(e))        
        
        return {
            '_type': "playlist",
            'id': "gaybeeg",
            'title': "gaybeeg",
            'entries': entries_final
        }               


