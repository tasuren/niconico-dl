# niconico_dl - Async Video Manager by tasuren

from typing import Optional

from aiofiles import open as async_open
from aiohttp import ClientSession
from json import loads, dumps
from bs4 import BeautifulSoup
import asyncio

from .templates import (
    _make_sessiondata, HEADERS, URLS, NicoNicoAcquisitionFailed
)


class NicoNicoVideoAsync:
    """ニコニコ動画の情報や動画を取得するためのクラスです。  
    このクラスから動画データの取得やダウンロードが行なえます。  
    ですがこれは非同期版です。(通常は`NicoNicoVideo`です。)

    Parameters
    ----------
    url : str
        ニコニコ動画のURLです。
    log : bool, default False
        ログ出力をするかどうかです。
    headers : dict, optional
        通信時に使用するヘッダーです。  
        デフォルトは`niconico_dl.HEADERS`が使われるので普通は変えなくて大丈夫です。
    loop : asyncio.AbstractLoop, optional
        使用するイベントループです。  
        指定しない場合は`asyncio.get_event_loop`によって自動で取得されます。

    Attributes
    ----------
    loop : asyncio.AbstractEventLoop
        使用しているイベントループです。
    heartbeat_task : asyncio.Task
        HeartbeatのTaskです。  
        Heartbeatを動かすまでこれはNoneです。

    SeeAlso
    -------
    NicoNicoVideo : このクラスの非非同期版です。"""
    def __init__(
        self, url: str, log: bool = False, headers: Optional[dict] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None
    ):
        self.loop: asyncio.AbstractEventLoop = loop or asyncio.get_event_loop()
        self._headers = headers or HEADERS
        self.heartbeat_task: asyncio.Task = None

        self._url, self._log = url, log
        self._data, self._download_link = {}, None
        self._session = ClientSession(raise_for_status=True)
        self._working_heartbeat = asyncio.Event()
        self._stop = False

    def print(self, *args, first: str = "", **kwargs) -> None:
        """niconico_dl用に用意したログ出力用の`print`です。"""
        if self._log:
            print(
                f"{first}[niconico_dl_async]",
                *args, **kwargs
            )

    async def __aenter__(self):
        # `async with`構文の最初に呼び出されるもの。
        # Heartbnneatを動かします。
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        # `async with`構文から抜けた際に呼び出されるもの。
        # Heartbeatをストップします。
        self.close()

    async def connect(self) -> None:
        """ニコニコ動画に接続します。  
        `download`を使用するにはこれを実行してからする必要があります。  
        そしてニコニコ動画との通信が終了したのなら`close`を実行する必要があります。

        Notes
        -----
        これと`close`は以下のように`async with`構文で省略が可能です。  
        ```python
        url = "https://www.nicovideo.jp/watch/sm9664372"
        async with niconico_dl.NicoNicoVideoAsync(url) as nico:
            await nico.download("video.mp4")
        ```"""
        self.heartbeat_task = self.loop.create_task(
            self._heartbeat(), name="niconico_dl.heartbeat"
        )
        await self.wait_until_working_heartbeat()

    def close(self, close_loop: bool = True) -> None:
        """NicoNicoVideoAsyncを終了します。  
        動画のダウンロードに必要な通信をするHeartbeatを止めます。  
        もし動画のダウンロードが終わったのならこれを実行してください。  
        `async with`構文を使用するのならこれを実行する必要はありません。  
        `async with`構文の使用例は`connect`にあります。

        Parameters
        ----------
        close_loop : bool, default True
            これの実行時に使用したイベントループも閉じるかどうかです。"""
        self._stop = True
        if close_loop and not self.loop.is_closed():
            self.loop.close()

    def __del__(self):
        self.close()

    async def get_info(self) -> dict:
        """ニコニコ動画のウェブページから動画のデータを取得するコルーチン関数です。

        Returns
        -------
        data : dict
            取得した動画の情報です。

        Raises
        ------
        NicoNicoAcquisitionFailed
            ニコニコ動画から情報を取得するのに失敗した際に発生します。"""
        self.print("Getting video data...")
        if not self._data:
            # もし動画データを取得していないなら動画URLのHTMLから動画データを取得する。
            # Heartbeatの通信にも必要なものでもあります。
            async with self._session.get(self._url, headers=self._headers[0]) as r:
                soup = BeautifulSoup(await r.text(), "html.parser")
                data = soup.find("div", {"id": "js-initial-watch-data"}).get("data-api-data")
                if data:
                    self._data = loads(data)
                else:
                    raise NicoNicoAcquisitionFailed("ニコニコ動画から情報を取得するのに失敗しました。")
        self.print("Done.")
        return self._data

    async def wait_until_working_heartbeat(self) -> None:
        """Heartbeatが動き出すまで待機します。"""
        await self._working_heartbeat.wait()

    def is_working_heartbeat(self) -> bool:
        """Heartbeatが動いているかの真偽値を返します。

        Returns
        -------
        is_working : bool
            Heartbeatが動いているかどうかの真偽値です。"""
        return self._working_heartbeat.is_set()

    async def get_download_link(self) -> str:
        """
        ニコニコ動画の動画のダウンロードリンクを取得します。  
        返されるリンクからはmp4の動画をダウンロードできます。

        Returns
        -------
        str : Download link

        Warnings
        --------
        返されるダウンロードリンクはHeartbeatが動いている間でしか使うことができません。  
        ですのでHeartbeatを止める`close`はダウンロードリンクの使用が終わってから実行しましょう。  
        したがって`async with`構文を使用して取得したダウンロードリンクはすぐに使えなくなることがあるので注意してください。
        """
        if self.download_link is None:
            # Heartbeatが動いていないなら動かす。
            if not self.is_working_heartbeat():
                await self.connect()
            # Heartbeatが動画のURLを取得するまで待機する。
            await self.wait_until_working_heartbeat()
            self.download_link = self.result_data["content_uri"]

        return self.download_link

    async def download(self, path: str, load_chunk_size: int = 1024) -> None:
        """ニコニコ動画の動画をダウンロードします。  
        mp4形式でダウンロードされます。

        Examples
        --------
        ```python
        url = "https://www.nicovideo.jp/watch/sm9720246"
        async with NicoNicoVideoAsync(url) as nico:
            data = await nico.get_info()
            title = data["video"]["title"]
            await nico.download(title + ".mp4")
        ```

        Notes
        -----
        もし`async with`構文を使用しないでダウンロードする場合は、ダウンロード前に`connect`を、ダウンロード終了後に`close`を実行してください。  
        動画データの通信に必要なHeartbeatが永遠に動き続けることになります。

        Parameters
        ----------
        path : str
            ダウンロードするニコニコ動画の動画の保存先です。
        load_chunk_size : int, default 1024
            一度にどれほどの量をダウンロードするかです。"""
        self.print("Now loading...")
        url = await self.get_download_link()

        params = (
            (
                "ht2_nicovideo",
                self.result_data["content_auth"]["content_auth_info"]["value"]
            ),
        )
        headers = self._headers[1]
        headers["Content-Type"] = "video/mp4"

        BASE = "Downloading video... :"
        self.print(BASE, "Now loading...", first="\r", end="")

        async with self._session.get(url, headers=headers, params=params) as r:
            size, now_size = r.content_length, 0

            self.print(BASE, "Making a null file...", first="\r", end="")

            async with async_open(path, "wb") as f:
                await f.write(b"")
            async with async_open(path, "ab") as f:
                async for chunk in r.content.iter_chunked(load_chunk_size):
                    if chunk:
                        now_size += len(chunk)
                        await f.write(chunk)
                        self.print(
                            BASE,
                            f"{int(now_size/size*100)}% ({now_size}/{size})",
                            first="\r", end=""
                        )

        self.print("Done.")

    async def _heartbeat(self, mode = "http_output_download_parameters") -> None:
        # Heartbeatです。
        self.print("Starting heartbeat...")
        if not self._data:
            await self.get_info()

        # セッションに必要なデータを`NicoNicoVideoAsync.get_info`で取得したデータから取得します。
        session = _make_sessiondata(
            self._data["media"]["delivery"]["movie"], mode=mode
        )
        self.print("Sending Heartbeat Init Data... :", dumps(session))

        # 一番最初のHeartbeatの通信をします。
        async with self._session.post(
            URLS["base_heartbeat"] + "?_format=json",
            headers=self._headers[1], json=session
        ) as r:
            self.result_data = (await r.json(loads=loads))["data"]["session"]
        session_id = self.result_data["id"]

        self.print("Done. session_id. : " + str(session_id))
        self._working_heartbeat.set()

        data = self.result_data
        while not self._stop:
            # ここで定期的にHeartbeatを送ります。
            await asyncio.sleep(
                data["keep_method"]["heartbeat"]["lifetime"] - 1
            )

            self.print("Sending heartbeat...", data)
            async with self._session.post(
                URLS["base_heartbeat"] + f"/{session_id}?_format=json&_method=PUT",
                headers=self._headers[1], json=data
            ) as r:
                self.result_data = (await r.json(loads=loads))["data"]["session"]

            self.print("Done.")
            data = {"session": self.result_data}
            self.print("Received data", data)

        self._session.close()