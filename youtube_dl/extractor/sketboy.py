# coding: utf-8
from __future__ import unicode_literals

import re
import random
import urllib.parse
import pprint

from .common import InfoExtractor
from ..utils import urlencode_postdata

class SketBoyIE(InfoExtractor):
    IE_NAME = 'sketboy'
    IE_DESC = 'sketboy'
    _VALID_URL = r"https?://(?:www\.)?sketboy.com"
    _LOGIN_URL = "https://www.sketboy.com/?"
    _LOGOUT_URL = "https://www.sketboy.com/es/?fn_logout=1"
    _SITE_URL = "https://www.sketboy.com"
    _SITE_CLOUD = "https://www.sketboy.com/api_admin.php?fn_cloudflare=1"
    _NETRC_MACHINE = 'hardkinks'


    def _login(self):
        username, password = self._get_login_info()
        if username is None:
            return

        
        data = {
            "redirect": "",
            "login[email]": username,
            "login[password]": password,
            "fn_login": ""
        }

        login_page, url_handle = self._download_webpage_handle(
            self._LOGIN_URL,
            None,
            note="Logging in",
            errnote="Login fail",
            data=urlencode_postdata(data),
            headers={
                "Referer": self._SITE_URL,
                "Origin": self._SITE_URL,
                "Upgrade-Insecure-Requests": "1",
                "Content-Type": "application/x-www-form-urlencoded",
                "Connection": "keep-alive",
            }
        )
        
    def _logout(self):
        self._request_webpage(
            self._LOGOUT_URL,
            None,
            'Log out'
        )


    def _real_initialize(self):
        self._login()

    def _real_extract(self, url):

        url = url.replace("detail", "regarder")
        
        content, url_handle = self._download_webpage_handle(
            url,
            None,
            'Downloading video page',
            headers={
                "Referer": self._SITE_URL,
                "Upgrade-Insecure-Requests": "1",
                "Connection": "keep-alive",
            }
        )
        #print(content)

        regex_mediaid = r"media_id: '(?P<mediaid>.*?)'"
        mobj = re.search(regex_mediaid, content)
        if mobj:
            media_id = mobj.group("mediaid")

        #print(media_id)

        data = { "media_id": media_id }

        info = self._download_json(
            self._SITE_CLOUD,
            None,
            note="JSON file",
            data=urlencode_postdata(data),
            headers={
                "Referer": url,
                "Origin": self._SITE_URL,
                "Upgrade-Insecure-Requests": "1",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Connection": "keep-alive",
                "X-Requested-With": "XMLHttpRequest"
            }
        )

        #pp = pprint.PrettyPrinter()
        #pp.pprint(info)

        title = info
        signed_id = info['stream']['signed_id']
        url_hls = "https://videodelivery.net/" + signed_id + "/manifest/video.m3u8"
        #url_dash = "https://videodelivery.net/" + signed_id + "/manifest/video.mpd"
        #print(url_hls)

        formats_m3u8 = self._extract_m3u8_formats(
            url_hls, None, m3u8_id="hls", fatal=False
        )

        #formats_mpd = self._extract_mpd_formats(
        #    url_dash, None, mpd_id="dash", fatal=False)

        self._sort_formats(formats_m3u8)

        #self._sort_formats(formats_mpd)

        self._logout()

        return {
            "id": info['stream']['id'],
            "title": title,
            #"formats": formats_mpd + formats_m3u8,
            "formats": formats_m3u8
        }

        
