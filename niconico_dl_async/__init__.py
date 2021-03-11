# niconico_dl_async by tasuren

from bs4 import BeautifulSoup as bs
from asyncio import get_event_loop
from aiohttp import ClientSession
from aiofile import async_open
from json import loads,dumps
from time import time


version = "1.0.0"


def par(max_num, now):
    return now/max_num*100

class NicoNico():
    def __init__(self, nicoid, log=False):
        self._print = lambda content,end="\n":print(content,end=end) if log else lambda: ""
        self.now_status = "..."
        self.url = None
        self.stop = True
        self.nicoid = nicoid
        self.now_downloading = False
        self.heartbeat_first_data = None
        self.tasks = []

    async def get_info(self):
        # 情報を取る。
        url = f"https://www.nicovideo.jp/watch/{self.nicoid}"
        self.headers = {
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

        self._print(f"Getting niconico webpage ... : {url}")

        async with ClientSession() as session:
            async with session.get(url, headers=self.headers) as res:
                html = await res.text()
        soup = bs(html, "html.parser")

        data = soup.find("div", {"id": "js-initial-watch-data"}).get("data-api-data")
        self.data = loads(data)
        self.dmc = self.data["video"]["dmcInfo"]

        # heartbeat用のdataを作る。
        data = self.dmc["session_api"]
        data["content_type"] = "movie"
        data["content_src_id_sets"] = [
            {
                "content_src_ids":[
                    {
                        "src_id_to_mux": {
                            "video_src_ids": data["videos"],
                            "audio_src_ids": [data["audios"][0]]
                        }
                    }
                ]
            }
        ]
        data["timing_constraint"] = "unlimited"
        data["keep_method"] = {
            "heartbeat": {
                "lifetime": data["heartbeat_lifetime"]
            }
        }
        data["protocol"] = {
            "name": "http",
            "parameters": {
                "http_parameters": {
                    "parameters": {
                        "http_output_download_parameters": {
                            "use_well_known_port": "yes" if data["urls"][0]["is_well_known_port"] else "no",
                            "use_ssl": "yes" if data["urls"][0]["is_ssl"] else "no",
                            "transfer_preset": "",
                            "segment_duration": 6000
                        }
                    }
                }
            }
        }
        data["content_uri"] = ""
        data["session_operation_auth"] = {
            "session_operation_auth_by_signature": {
                "token": data["token"],
                "signature": data["signature"]
            }
        }
        data["content_auth"] = {
            "auth_type": data["auth_types"]["http"],
            "content_key_timeout": data["content_key_timeout"],
            "service_id": "nicovideo",
            "service_user_id": str(data["service_user_id"])
        }
        data["client_info"] = {
            "player_id": data["player_id"]
        }

        self.heartbeat_first_data = {"session": data}

        return self.data

    async def start_stream(self):
        # 定期的に生きていることをニコニコに伝えるためのもの。
        if not self.heartbeat_first_data:
            await self.get_info()
        self.get = False
        second_get = False
        c = 0

        async with ClientSession(raise_for_status=True) as session:
            self._print("Starting heartbeat ... : https://api.dmc.nico/api/sessions?_format=json")
            async with session.post(
                f"https://api.dmc.nico/api/sessions?_format=json",
                headers=self.headers,
                data=dumps(self.heartbeat_first_data)
            ) as res:
                self.result_data = loads(await res.text())["data"]["session"]
                session_id = self.result_data["id"]
                self.now_status = f"HeartBeat - {res.status}, next - ..."

            self.get = True

            before = time()
            while not self.stop:
                now = time()

                if second_get and self.tasks:
                    for task in self.tasks:
                        if not task.is_alive():
                            task.start()
                            self.tasks.pop(0)

                if now > before + 30:
                    async with session.post(
                        f"https://api.dmc.nico/api/sessions/{session_id}?_format=json&_method=PUT",
                        headers=self.headers,
                        data=dumps({"session": self.result_data})
                    ) as res:

                        self.now_status = f"HeartBeat - {res.status}, next - {now + 30}"

                        if res.status == 201 or res.status == 200:
                            self.result_data = loads(await res.text())["data"]["session"]
                    before = now
                elif now > before + 5 and not second_get:
                    res = post(
                        f"https://api.dmc.nico/api/sessions/{session_id}?_format=json&_method=PUT",
                        headers=self.headers
                    )
                    second_get = True
                elif now > before + 1 and not self.now_downloading:
                    c += 1
                    if c == 3:
                        break
                elif now > before + 3 and self.now_downloading:
                    c = 0

    async def get_download_link(self):
        if self.stop:
            self.stop = False
            await self.start_stream()
            self.now_downloading = True

            # 心臓が動くまで待機。
            while not self.get:
                pass

            return self.result_data["content_uri"]
        else:
            return self.result_data["content_uri"]

    async def download(self, path, chunk=1024):
        self.url = url = await self.get_download_link()

        params = (
            (
                "ht2_nicovideo",
                self.result_data["content_auth"]["content_auth_info"]["value"]
            ),
        )
        headers = self.headers
        headers["Content-Type"] = "video/mp4"

        self._print(f"Getting file size ...")
        async with ClientSession(raise_for_status=True) as session:
            self._print(f"Starting download ... : {url}")
            async with session.get(
                url,
                headers=self.headers,
                params=params,
            ) as res:

                size = res.content_length

                now_size = 0
                async with async_open(path, "wb") as f:
                    await f.write(b"")
                async with async_open(path, "ab") as f:
                    async for chunk in res.content.iter_chunked(chunk):
                        if chunk:
                            now_size += len(chunk)
                            await f.write(chunk)
                            self._print(
                                f"\rDownloading now ... : {int(now_size/size*100)}% ({now_size}/{size}) | Response status : {self.now_status}",
                                end=""
                            )
        self._print("\nDownload was finished.")
        self.now_downloading = False

    def close(self):
        self.stop = True

    def __del__(self):
        self.close()


if __name__ == "__main__":
    async def test():
        niconico = NicoNico("sm20780163", log=True)
        data = await niconico.get_info()
        print(await niconico.get_download_link())
        input()
        niconico.close()
    get_event_loop().run_until_complete(test())