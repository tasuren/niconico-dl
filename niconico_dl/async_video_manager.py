# niconico_dl - Async Video Manager by tasuren

from bs4 import BeautifulSoup as bs
from aiohttp import ClientSession
from ujson import loads, dumps
from time import time
import asyncio

from .__init__ import HEADERS, make_sessiondata


URLS = {
    "base_heartbeat": "https://api.dmc.nico/api/sessions"
}


class NicoNicoVideoAsync:
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
        self.data = {}
        self.session = ClientSession(raise_for_status=True)
        self.working_heartbeat = asyncio.Event()
        self.stop = False

    async def get_info(self) -> dict:
        """
        ニコニコ動画のウェブページから動画のデータを取得するコルーチン関数です。

        Returns
        -------
        data : dict
            取得した動画の情報です。

        Raises
        ------
        NicoNicoAcquisitionFailed
            ニコニコ動画から情報を取得するのに失敗した際に発生します。
        """
        self.print("Getting video data...")
        async with self.session.get(self.url, headers=self.headers) as r:
            if not self.data:
                soup = bs(await r.text(), "html.parser")
                data = soup.find("div", {"id": "js-initial-watch-data"}).get("data-api-data")
                if data:
                    self.data = loads(data)
                else:
                    raise NicoNicoAcquisitionFailed("ニコニコ動画から情報を取得するのに失敗しました。")
        self.print("Done.")
        return self.data

    async def wait_until_working_heartbeat(self):
        """
        Heartbeatが動き出すまで待機します。
        """
        await self.working_heartbeat.wait()

    def is_working_heartbeat(self) -> bool:
        """
        Heartbeatが動いているかの真偽値を返します。

        Returns
        -------
        is_working : bool
            Heartbeatが動いているかどうかの真偽値です。
        """
        return self.working_heartbeat.is_set()

    async def heartbeat(self):
        self.print("Starting heartbeat...")
        if not self.data:
            await self.get_info()
        session = make_sessiondata(self.data["media"]["delivery"]["movie"])
        self.print("Sending Heartbeat Init Data...")
        async with self.session.post(
                URLS["base_heartbeat"] + "?_format=json",
                headers=self.headers, data=dumps(session)) as r:
            self.result_data = (await r.json(loads=loads))["data"]["session"]
        session_id = self.result_data["id"]
        self.print("Done. session_id. : " + str(session_id))
        self.working_heartbeat.set()

        before, data = time(), None
        while not self.stop:
            now = time()
            self.print("Sending heartbeat...")
            async with self.session.post(
                    URLS["base_heartbeat"] + f"/{session_id}?_format=json&_method=PUT",
                    headers=self.headers, data=data) as r:
                self.result_data = (await r.json(loads=loads))["data"]["session"]
            self.print("Done.")
            data = dumps({"session": self.result_data})
            await asyncio.sleep(40)
