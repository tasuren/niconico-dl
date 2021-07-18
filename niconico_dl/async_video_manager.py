# niconico_dl - Async Video Manager by tasuren

from aiofiles import open as async_open
from aiohttp import ClientSession
from ujson import loads, dumps
from bs4 import BeautifulSoup
import asyncio

from .__init__ import HEADERS, MODES, make_sessiondata


URLS = {
    "base_heartbeat": "https://api.dmc.nico/api/sessions"
}


class NicoNicoVideoAsync:
    """
    ニコニコ動画の情報や動画を取得するためのクラスです。  
    このクラスから動画データの取得やダウンロードが行なえます。  
    ですがこれは非同期版です。(通常は`NicoNicoVideo`です。)

    Parameters
    ----------
    url : str
        ニコニコ動画のURLです。
    log : bool, default False
        ログ出力をするかどうかです。

    Attributes
    ----------
    data : dict
        動画のデータです。  
        `NicoNicoVideoAsync.get_info`を実行するまでこれは空です。    

    SeeAlso
    -------
    NicoNicoVideo : ニコニコ動画の情報や動画を取得するためのクラスです。
    """
    def __init__(self, url: str, log: bool = False, headers: dict = HEADERS):
        self.headers, self.url, self.log = headers, url, log
        self.data, self.download_link = {}, None
        self.session = ClientSession(raise_for_status=True)
        self.working_heartbeat = asyncio.Event()
        self.loop = asyncio.get_event_loop()
        self.stop = False

    def print(self, *args, no_n: bool = False):
        """
        ログ出力を楽に行うためのもの。
        """
        if self.log:
            no_n = ("\r", "") if no_n else ("", "\n")
            print(no_n[0] + "[niconico_dl_async]", *args, end=no_n[1])

    async def __aenter__(self):
        # `async with`構文の最初に呼び出されるもの。
        # Heartbnneatを動かします。
        self.loop.create_task(self.heartbeat())
        return self

    async def __aexit__(self, exc_type, exc, tb):
        # `async with`構文から抜けた際に呼び出されるもの。
        # Heartbeatをストップします。
        self.close()

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
        if not self.data:
            # もし動画データを取得していないなら動画URLのHTMLから動画データを取得する。
            # Heartbeatの通信にも必要なものでもあります。
            async with self.session.get(self.url, headers=self.headers[0]) as r:
                soup = BeautifulSoup(await r.text(), "html.parser")
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

    async def get_download_link(self) -> str:
        """
        ニコニコ動画の動画のダウンロードリンクを取得します。  
        返されるリンクからはmp4の動画をダウンロードできます。

        Notes
        -----
        返されるダウンロードリンクはHeartbeatが動いている間でしか使うことができません。  
        ですのでHeartbeatを止める`NicoNicoVideoAsync.close`はダウンロードリンクの使用が終わってから実行しましょう。  
        したがって`async with`構文を使用して取得したダウンロードリンクはすぐに使えなくなることがあるので注意してください。
        """
        if self.download_link is None:
            # Heartbeatが動いていないなら動かす。
            if not self.is_working_heartbeat:
                self.loop.create_task(self.heartbeat())
            # Heartbeatが動画のURLを取得するまで待機する。
            await self.wait_until_working_heartbeat()
            self.download_link = self.result_data["content_uri"]
        return self.download_link

    async def download(self, path: str, load_chunk_size: int = 1024):
        """
        ニコニコ動画の動画をダウンロードします。  
        mp4形式でダウンロードされます。

        Examples
        --------
        url = "https://www.nicovideo.jp/watch/sm9720246"
        async with NicoNicoVideoAsync(url) as nico:
            data = await nico.get_info()
            title = data["video"]["title"]
            await nico.download(title)

        Notes
        -----
        もし`async with`構文を使用しないでダウンロードする場合は、ダウンロード終了後に`NicoNicoVideoAsync.close`を実行してください。  
        動画データの通信に必要なHeartbeatが永遠に動き続けることになります。

        Parameters
        ----------
        path : str
            ダウンロードするニコニコ動画の動画の保存先です。
        load_chunk_size : int, default 1024
            一度にどれほどの量をダウンロードするかです。
        """
        self.print("Now loading...")
        url = await self.get_download_link()
        params = (
            (
                "ht2_nicovideo",
                self.result_data["content_auth"]["content_auth_info"]["value"]
            ),
        )
        headers = self.headers[1]
        headers["Content-Type"] = "video/mp4"
        BASE = "Downloading video... :"

        self.print(BASE, "Now loading...", no_n=True)
        async with self.session.get(url, headers=headers, params=params) as r:
            size, now_size = r.content_length, 0

            self.print(BASE, "Making null file...", no_n=True)
            async with async_open(path, "wb") as f:
                await f.write(b"")
            async with async_open(path, "ab") as f:
                async for chunk in r.content.iter_chunked(load_chunk_size):
                    if chunk:
                        now_size += len(chunk)
                        await f.write(chunk)
                        self.print(BASE, f"{int(now_size/size*100)}% ({now_size}/{size})")
        self.print("Done.")

    def close(self):
        """
        NicoNicoVideoAsyncを終了します。  
        動画のダウンロードに必要な通信をするHeartbeatを止めます。  
        もし動画のダウンロードが終わったのならこれを実行してください。  
        `async with`構文を使用するのならこれを実行する必要はありません。
        """
        self.stop = True

    async def heartbeat(self, mode: str = "http_output_download_parameters"):
        """
        動画データの通信に必要なHeartbeatです。  
        `NicoNicoVideoAsync.get_download_link`を実行すると自動で作動するので通常はこれを動かさなくて大丈夫です。

        See Also
        --------
        get_download_link : ニコニコ動画の動画のmp4形式のファイルのダウンロードリンクを取得します。
        download : ニコニコ動画の動画をmp4形式でダウンロードします。

        Parameters
        ----------
        mode : str, default "http_output_download_parameters"
            通信する動画ファイルのタイプです。
            tsファイルの`"hls_parameters"`かmp4の`"http_output_download_parameters"`が使えます。
        """
        self.print("Starting heartbeat...")
        if not self.data:
            await self.get_info()
        # セッションに必要なデータを`NicoNicoVideoAsync.get_info`で取得したデータから取得します。
        session = make_sessiondata(self.data["media"]["delivery"]["movie"], mode=mode)
        self.print("Sending Heartbeat Init Data... :", dumps(session))
        # 一番最初のHeartbeatの通信をします。
        async with self.session.post(
                URLS["base_heartbeat"] + "?_format=json",
                headers=self.headers[1], data=dumps(session)) as r:
            self.result_data = (await r.json(loads=loads))["data"]["session"]
        session_id = self.result_data["id"]
        self.print("Done. session_id. : " + str(session_id))
        self.working_heartbeat.set()

        data = None
        while not self.stop:
            # ここで定期的にHeartbeatの「生存してるお。」を送ります。
            await asyncio.sleep(40)
            self.print("Sending heartbeat...")
            async with self.session.post(
                    URLS["base_heartbeat"] + f"/{session_id}?_format=json&_method=PUT",
                    headers=self.headers[1], data=data) as r:
                self.result_data = (await r.json(loads=loads))["data"]["session"]
            self.print("Done.")
            data = dumps({"session": self.result_data})
