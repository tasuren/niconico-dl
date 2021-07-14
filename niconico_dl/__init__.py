"""
.. include:: ../README.md
"""

from .async_video_manager import *


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


def make_sessiondata(movie: dict) -> dict:
    # 動画データからニコニコとの通信に使うセッションデータを作る関数。
    data = {}
    session =  movie["session"]

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

    return {"session": data}
