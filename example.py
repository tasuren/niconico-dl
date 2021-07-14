# niconico_dl example

import niconico_dl
import asyncio


async def start():
    video = niconico_dl.NicoNicoVideoAsync("https://www.nicovideo.jp/watch/sm9664372", log=True)
    await video.heartbeat()


asyncio.run(start())
