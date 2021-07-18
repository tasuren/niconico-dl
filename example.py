# niconico_dl example

import niconico_dl
import asyncio


async def start():
    url = "https://www.nicovideo.jp/watch/sm9664372"
    async with niconico_dl.NicoNicoVideoAsync(url, log=True) as nico:
        data = await nico.get_info()
        await nico.download(data["video"]["title"] + ".mp4")


asyncio.run(start())
