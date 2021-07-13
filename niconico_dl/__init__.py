"""
.. include:: ../README.md
"""

from asyncio_video_manager import *


__version__ = "1.0.0a1"


__all__ = ("HEADERS", "NicoNicoAcquisitionFailed", "NicoNicoVideoAsync")
"""リファレンスに載せるもののリストです。"""
HEADERS = {
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Allow-Origin": "https://www.nicovideo.jp",
    'Connection': 'keep-alive',
    "Content-Type": "application/json",
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.72 Safari/537.36 Edg/89.0.774.45',
    'Accept': '*/*',
    "Accept-Encoding": "gzip, deflate, br",
    'Origin': 'https://www.nicovideo.jp',
    'Sec-Fetch-Site': 'cross-site',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Dest': 'empty',
    "Origin": "https://www.nicovideo.jp",
    "Referer": "https://www.nicovideo.jp/",
    "Sec-Fetch-Dest": "empty",
    'Accept-Language': 'ja,en;q=0.9,en-GB;q=0.8,en-US;q=0.7'
}
"""通信に使うヘッダーです。"""


class NicoNicoAcquisitionFailed(Exception):
    """
    これはニコニコとの通信で何かしら失敗した際に発生します。
    """
    pass
