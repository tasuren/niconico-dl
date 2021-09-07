# niconico_dl
ニコニコ動画にある動画をダウンロードするためのPython用のライブラリです。

## Install
`pip install niconico_dl`

## Examples
### Normal
```python
url = "https://www.nicovideo.jp/watch/sm38533566"

with niconico_dl.NicoNicoVideo(url, log=True) as nico:
    data = nico.get_info()
    nico.download(data["video"]["title"] + ".mp4")

print("Downloaded!")
```
### Async
```python
async def start_async():
    url = "https://www.nicovideo.jp/watch/sm9664372"
    async with niconico_dl.NicoNicoVideoAsync(url, log=True) as nico:
        data = await nico.get_info()
        await nico.download(data["video"]["title"] + ".mp4")
    print("Downloaded!")


asyncio.run(start_async())
```
### Command Line
使用方法：`niconico_dl [URL]`  
ダウンロードした動画は`output.mp4`という名前で実行したディレクトリに保存されます。