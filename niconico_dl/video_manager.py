# niconico_dl - Video Manager

from typing import Optional

from json import loads, dumps
from bs4 import BeautifulSoup
from threading import Thread
from time import sleep, time
import requests

from .templates import (
    _make_sessiondata, HEADERS, URLS, NicoNicoAcquisitionFailed
)


class NicoNicoVideo:
    """ニコニコ動画の情報や動画を取得するためのクラスです。  
    このクラスから動画データの取得やダウンロードが行なえます。

    Parameters
    ----------
    url : str
        ニコニコ動画のURLです。
    log : bool, default False
        ログ出力をするかどうかです。
    headers : dict, Optional
        通信時に使用するヘッダーです。  
        指定されない場合は`niconico_dl.HEADERS`を使用するので普通は変えなくて大丈夫です。

    Attributes
    ----------
    heartbeat_thread : threading.Thread
        Heartbeatのスレッドです。  
        Heartbeatを動かすまでこれはNoneです。

    SeeAlso
    -------
    NicoNicoVideoAsync : このクラスの非同期バージョンです。"""
    def __init__(
        self, url: str, log: bool = False, headers: Optional[dict] = None
    ):
        self._headers = headers or HEADERS
        self.heartbeat_thread: Thread = None

        self._url, self._log = url, log
        self._data, self._download_link = {}, None
        self._working_heartbeat = False
        self._stop = False

    def print(self, *args, first: str = "", **kwargs) -> None:
        """niconico_dl用に用意したログ出力用の`print`です。"""
        if self._log:
            print(
                f"{first}[niconico_dl]",
                *args, **kwargs
            )

    def __enter__(self):
        # `with`構文の最初に呼び出されるもの。
        # Heartbnneatを動かします。
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb):
        # `with`構文から抜けた際に呼び出されるもの。
        # Heartbeatをストップします。
        self.close()

    def connect(self) -> None:
        """ニコニコ動画に接続します。  
        `download`を使用するにはこれを実行してからする必要があります。  
        そしてニコニコ動画との通信が終了したのなら`close`を実行する必要があります。

        Notes
        -----
        これと`close`は以下のように`with`構文で省略が可能です。  
        ```python
        url = "https://www.nicovideo.jp/watch/sm15713037"
        with niconico_dl.NicoNicoVideo(url) as nico:
            nico.download("video.mp4")
        ```"""
        self.heartbeat_thread = Thread(
            target=self._heartbeat,
            name="niconico_dl.heartbeat"
        )
        self.heartbeat_thread.start()
        self.wait_until_working_heartbeat()

    def close(self, close_loop: bool = True) -> None:
        """NicoNicoVideoAsyncを終了します。  
        動画のダウンロードに必要な通信をするHeartbeatを止めます。  
        もし動画のダウンロードが終わったのならこれを実行してください。  
        `with`構文を使用するのならこれを実行する必要はありません。  
        `with`構文の使用例は`connect`の説明にあります。"""
        self._stop = True
        self.heartbeat_thread.join()

    def __del__(self):
        self.close()

    def get_info(self) -> dict:
        """ニコニコ動画のウェブページから動画のデータを取得する関数です。

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
            soup = BeautifulSoup(
                requests.get(self._url, headers=self._headers[0]).text,
                "html.parser"
            )
            data = soup.find(
                "div", {"id": "js-initial-watch-data"}
            ).get("data-api-data")
            if data:
                self._data = loads(data)
            else:
                raise NicoNicoAcquisitionFailed("ニコニコ動画から情報を取得するのに失敗しました。")
        self.print("Done.")
        return self._data

    def wait_until_working_heartbeat(self) -> None:
        """Heartbeatが動き出すまで待機します。"""
        while not self._working_heartbeat:
            pass

    def is_working_heartbeat(self) -> bool:
        """Heartbeatが動いているかの真偽値を返します。

        Returns
        -------
        is_working : bool
            Heartbeatが動いているかどうかの真偽値です。"""
        return self._working_heartbeat

    def get_download_link(self) -> str:
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
        したがって`with`構文を使用して取得したダウンロードリンクはすぐに使えなくなることがあるので注意してください。
        """
        if self._download_link is None:
            # Heartbeatが動いていないなら動かす。
            if not self.is_working_heartbeat():
                self.connect()
            # Heartbeatが動画のURLを取得するまで待機する。
            self.wait_until_working_heartbeat()
            self._download_link = self.result_data["content_uri"]

        return self._download_link

    def download(self, path: str, load_chunk_size: int = 1024) -> None:
        """ニコニコ動画の動画をダウンロードします。  
        mp4形式でダウンロードされます。

        Examples
        --------
        ```python
        url = "https://www.nicovideo.jp/watch/sm1097445"
        with NicoNicoVideo(url) as nico:
            data = nico.get_info()
            title = data["video"]["title"]
            nico.download(title + ".mp4")
        ```

        Notes
        -----
        もし`with`構文を使用しないでダウンロードする場合は、ダウンロード前に`connect`を、ダウンロード終了後に`close`を実行してください。  
        動画データの通信に必要なHeartbeatが永遠に動き続けることになります。

        Parameters
        ----------
        path : str
            ダウンロードするニコニコ動画の動画の保存先です。
        load_chunk_size : int, default 1024
            一度にどれほどの量をダウンロードするかです。"""
        self.print("Now loading...")
        url = self.get_download_link()

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

        size = int(
            requests.head(
                url, headers=headers, params=params
            ).headers.get("content-length")
        )

        r = requests.get(url, headers=headers, params=params, stream=True)
        r.raise_for_status()
        now_size = 0

        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=load_chunk_size):
                if chunk:
                    now_size += len(chunk)
                    f.write(chunk)
                    self.print(
                        BASE,
                        f"{int(now_size/size*100)}% ({now_size}/{size})",
                        first="\r", end=""
                    )

        self.print("Done.", first="\n")

    def _heartbeat(self, mode = "http_output_download_parameters") -> None:
        # Heartbeatです。
        self.print("Starting heartbeat...")
        if not self._data:
            self.get_info()

        # セッションに必要なデータを`NicoNicoVideoAsync.get_info`で取得したデータから取得します。
        session = _make_sessiondata(
            self._data["media"]["delivery"]["movie"], mode=mode
        )
        self.print("Sending Heartbeat Init Data... :", dumps(session))

        # 一番最初のHeartbeatの通信をします。
        r = requests.post(
            URLS["base_heartbeat"] + "?_format=json",
            headers=self._headers[1], data=dumps(session)
        )
        self.result_data = r.json()["data"]["session"]
        session_id = self.result_data["id"]

        self.print("Done. session_id. : " + str(session_id))
        self._working_heartbeat = True

        data = self.result_data
        after = time() + data["keep_method"]["heartbeat"]["lifetime"] - 1
        while not self._stop:
            now = time()
            # ここで定期的にHeartbeatを送ります。
            if now >= after:
                self.print("Sending heartbeat...", data)
                r = requests.post(
                    URLS["base_heartbeat"] + f"/{session_id}?_format=json&_method=PUT",
                    headers=self._headers[1], data=dumps(data)
                )
                self.result_data = r.json()["data"]["session"]

                self.print("Done.")
                data = {"session": self.result_data}
                self.print("Received data", data)

                after = now + data["keep_method"]["heartbeat"]["lifetime"] - 1
            else:
                sleep(0.05)