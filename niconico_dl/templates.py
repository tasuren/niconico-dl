# niconico_dl - Templates

from copy import copy


"""リファレンスに載せるもののリストです。"""
HEADERS = [
    {
        "Host": "www.nicovideo.jp",
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0",
        "sec-ch-ua": 'Chromium";v="92", " Not A;Brand";v="99", "Microsoft Edge";v="92',
        "sec-ch-ua-mobile": "?0",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.40 Safari/537.36 Edg/92.0.902.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-User": "?1",
        "Sec-Fetch-Dest": "document",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "ja,en;q=0.9,en-GB;q=0.8,en-US;q=0.7"
    },
    {
        "Connection": "keep-alive",
        "sec-ch-ua": '"Chromium";v="92", " Not A;Brand";v="99", "Microsoft Edge";v="92"',
        "Accept": "application/json",
        "sec-ch-ua-mobile": "?0",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.40 Safari/537.36 Edg/92.0.902.9",
        "Content-Type": "application/json",
        "Origin": "https://www.nicovideo.jp",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://www.nicovideo.jp/",
        "Accept-Language": "ja,en;q=0.9,en-GB;q=0.8,en-US;q=0.7"
    }
]
MODES = ("hls_parameters", "http_output_download_parameters") 


URLS = {
    "base_heartbeat": "https://api.dmc.nico/api/sessions"
}


def _make_sessiondata(movie: dict, mode: str = MODES[0]) -> dict:
    # 動画データからニコニコとの通信に使うセッションデータを作る関数。
    data = {}
    session =  movie["session"]

    data["content_type"] = "movie"
    data["content_src_id_sets"] = [{"content_src_ids": []}]
    lv, la = len(session["videos"]), len(session["audios"])
    for _ in range(lv if lv >= la else la):
        src_id_to_mux = {
            "src_id_to_mux": {
                "video_src_ids": copy(session["videos"]),
                "audio_src_ids": copy(session["audios"])
            }
        }
        data["content_src_id_sets"][0]["content_src_ids"].append(src_id_to_mux)
        if mode == MODES[1]:
            break
        for k in ("videos", "audios"):
            if len(session[k]) != 1:
                session[k].pop(0)
    del src_id_to_mux
    data["timing_constraint"] = "unlimited"
    data["keep_method"] = {
        "heartbeat": {
            "lifetime": session["heartbeatLifetime"]
        }
    }
    data["recipe_id"] = session["recipeId"]
    data["priority"] = session["priority"]
    if mode in MODES:
        parameters = {
            MODES[1]: {
                "use_well_known_port": "yes" if session["urls"][0]["isWellKnownPort"] else "no",
                "use_ssl": "yes" if session["urls"][0]["isSsl"] else "no",
                "transfer_preset": ""
            }
        }
        if mode == MODES[0]:
            parameters[MODES[0]] = parameters[MODES[1]]
            parameters[MODES[0]]["segment_duration"] = 6000
            del parameters[MODES[1]]
    else:
        raise ValueError("modeは`hls_parameters`か`http_output_download_parameters`である必要があります。")
    data["protocol"] = {
        "name": "http",
        "parameters": {
            "http_parameters": {
                "parameters": parameters
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
    del session, movie

    return {"session": data}


class NicoNicoAcquisitionFailed(Exception):
    """ニコニコ動画から情報を取得するのに失敗した際に発生するもの。"""
    pass