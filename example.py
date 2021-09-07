# niconico_dl example

import niconico_dl
import asyncio


# Normal
def start():
    url = "https://www.nicovideo.jp/watch/sm9664372"
    with niconico_dl.NicoNicoVideo(url, log=True) as nico:
        data = nico.get_info()
        nico.download(data["video"]["title"] + ".mp4")
    print("Downloaded!")


start()


# Async Version
async def start_async():
    url = "https://www.nicovideo.jp/watch/sm9664372"
    async with niconico_dl.NicoNicoVideoAsync(url, log=True) as nico:
        data = await nico.get_info()
        await nico.download(data["video"]["title"] + ".mp4")
    print("Downloaded!")


asyncio.run(start_async())
