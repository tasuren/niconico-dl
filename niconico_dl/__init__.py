# niconico_dl by tasuren

from bs4 import BeautifulSoup as bs
from requests import post,get,head
from threading import Thread
from json import loads,dumps
from time import time


version = "1.1.2"


class NicoNico():
    def __init__(self, nicoid, log=False):
        self._print = lambda content,end="\n":print(content,end=end) if log else lambda: ""
        self.now_status = "..."
        self.stop = False
        self.nicoid = nicoid
        self.now_downloading = False
        self.tasks = []

        # 情報を取る。
        url = f"https://www.nicovideo.jp/watch/{nicoid}"
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

        html = get(url, headers=self.headers).text
        soup = bs(html, "html.parser")

        data = soup.find("div", {"id": "js-initial-watch-data"}).get("data-api-data")
        self.data = loads(data)
        movie = self.data["media"]["delivery"]["movie"]

        # heartbeat用のdataを作る。
        session =  movie["session"]
        data = {}
        data["content_type"] = "movie"
        data["content_src_id_sets"] = [
            {
                "content_src_ids":[
                    {
                        "src_id_to_mux": {
                            "video_src_ids": [movie["videos"][0]["id"]],
                            "audio_src_ids": [movie["audios"][0]["id"]]
                        }
                    }
                ]
            }
        ]
        data["timing_constraint"] = "unlimited"
        data["keep_method"] = {
            "heartbeat": {
                "lifetime": session["heartbeatLifetime"]
            }
        }
        data["recipe_id"] = session["recipeId"]
        data["priority"] = session["priority"]
        data["protocol"] = {
            "name": "http",
            "parameters": {
                "http_parameters": {
                    "parameters": {
                        "http_output_download_parameters": {
                            "use_well_known_port": "yes" if session["urls"][0]["isWellKnownPort"] else "no",
                            "use_ssl": "yes" if session["urls"][0]["isSsl"] else "no",
                            "transfer_preset": ""
                        }
                    }
                }
            }
        }
        data["content_uri"] = ""
        data["session_operation_auth"] = {
            "session_operation_auth_by_signature": {
                "token": session["token"],
                "signature": session["signature"]
            }
        }
        data["content_id"] = session["contentId"]
        data["content_auth"] = {
            "auth_type": session["authTypes"]["http"],
            "content_key_timeout": session["contentKeyTimeout"],
            "service_id": "nicovideo",
            "service_user_id": str(session["serviceUserId"])
        }
        data["client_info"] = {
            "player_id": session["playerId"]
        }

        # 心臓を稼働させる。
        Thread(target=self.start_stream, args=({"session": data},)).start()

    def start_stream(self, data):
        # 定期的に生きていることをニコニコに伝えるためのもの。
        self.get = False
        second_get = False
        c = 0

        self._print("Starting heartbeat ... : https://api.dmc.nico/api/sessions?_format=json")
        res = post(
            f"https://api.dmc.nico/api/sessions?_format=json",
            headers=self.headers,
            data=dumps(data)
        )

        self.result_data = loads(res.text)["data"]["session"]
        session_id = self.result_data["id"]

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
                res = post(
                    f"https://api.dmc.nico/api/sessions/{session_id}?_format=json&_method=PUT",
                    headers=self.headers,
                    data=dumps({"session": self.result_data})
                )

                self.now_status = f"HeartBeat - {res}, next - {now + 30}"

                if res.status_code == 201 or res.status_code == 200:
                    self.result_data = loads(res.text)["data"]["session"]
                else:
                    raise 
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

    def get_download_link(self):
        self.now_downloading = True

        # 心臓が動くまで待機。
        while not self.get:
            pass

        return self.result_data["content_uri"]

    def download(self, path, timeout=5, chunk_size=8192):
        url = self.get_download_link()

        params = (
            (
                "ht2_nicovideo",
                self.result_data["content_auth"]["content_auth_info"]["value"]
            ),
        )
        headers = self.headers
        headers["Content-Type"] = "video/mp4"

        self._print(f"Getting file size ...")
        size = int(
            head(
                url,
                headers=headers,
                params=params
            ).headers.get("content-length")
        )

        self._print(f"Starting download ... : {url}")
        res = get(
            url,
            headers=self.headers,
            params=params,
            stream=True,
            timeout=timeout
        )

        res.raise_for_status()

        now_size = 0
        with open(path[:-1]+"4", "wb") as f:
            for chunk in res.iter_content(chunk_size=chunk_size):
                if chunk:
                    now_size += len(chunk)
                    f.write(chunk)
                    f.flush()
                    self._print(
                        f"\rDownloading now ... : {now_size}/{size} | Response status : {self.now_status}",
                        end=""
                    )
        self._print("\nDownload was finished.")
        self.now_downloading = False

    def close(self):
        self.stop = True

    def __del__(self):
        self.close()



if __name__ == "__main__":
    niconico = NicoNico("sm20780163", log=True)
    niconico.download(niconico.data["video"]["title"]+".mp3", convert_to_mp3=True)
    niconico.close()