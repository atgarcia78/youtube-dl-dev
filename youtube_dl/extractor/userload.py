from __future__ import unicode_literals


import re
from .common import InfoExtractor, ExtractorError
from ..utils import (
    urlencode_postdata,
    sanitize_filename

)

class UserLoadIE(InfoExtractor):

    IE_NAME = 'userload'
    _VALID_URL = r'https?://(?:www\.)?userload\.co'

    
    def _real_extract(self, url):
        
   
     
        webpage = self._download_webpage(url, None, headers = {"Alt-Used": "userload.co", "Referer": "https://www.myvidster.com"})
        

        #self.to_screen(webpage)      
        
        data = re.findall(r"var\|\|([^\']*)\'", webpage)
        _data = None
        if data:
            _data = data[0].split('|')
        
        if not _data:
            raise ExtractorError("No video data")
        
        #self.to_screen(data)
        
        data = {
            "morocco": _data[2],
            "mycountry": _data[-2],
        }

        video_info = self._download_webpage(
            "https://userload.co/api/request/",
            None,
            data=urlencode_postdata(data),
            headers={
                "Referer": url,
                "Origin": "https://userload.co",
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        
        #self.to_screen(video_info)
        
        if not video_info or not video_info.startswith("http"):
            raise ExtractorError("No video data after api request")
            
        

        entry_video = {
            '_type' : 'url',
            'url' : video_info,
            'id' : _data[0],
            'title' : _data[8]
            }

        return entry_video


