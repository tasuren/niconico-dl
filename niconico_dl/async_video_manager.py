# niconico_dl - Async Video Manager by tasuren

from bs4 import BeautifulSoup as bs
from aiohttp import ClientSession
from ujson import loads, dumps
from time import time
import asyncio

from __init__ import HEADERS


class NicoNicoVideoAsync(ClientSession):
    """
    ニコニコ動画の情報や動画を取得するためのクラスです。  
    ですがこれは非同期版です。(通常は`NicoNicoVideo`です。)

    Parameters
    ----------
    url : str
        ニコニコ動画のURLです。
    log : bool, default False
        ログ出力をするかどうかです。

    SeeAlso
    -------
    NicoNicoVideo : ニコニコ動画の情報や動画を取得するためのクラスです。
    """
    def __init__(self, url: str, log: bool = False, headers: dict = HEADERS):
        self.print = ((lambda content: print("[niconico_dl_async]", content))
                      if log else lambda content: "")
        self.headers, self.url = headers, url
        self.data
        self.loop = asyncio.get_event_loop()
        super().__init__(raise_for_status=True, loop=self.loop)

    async def get_info(self) -> dict:
        """
        ニコニコ動画のウェブページから動画のデータを取得するコルーチン関数です。
        """
        async with self.get(self.url, headers=HEADERS) as r:
            html = bs(await r.text(), "html.parser")
            data = soup.find("div", {"id": "js-initial-watch-data"}).get("data-api-data")
            if data:
                self.data = loads(data)
                data = self.data["media"]["delivery"]["movie"]
            else:
                raise NicoNicoAcquisitionFailed()
