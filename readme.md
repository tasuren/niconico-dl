![PyPI](https://img.shields.io/pypi/v/niconico-dl) ![PyPI - Downloads](https://img.shields.io/pypi/dm/niconico_dl)
# niconico_dl
ニコニコ動画にある動画をダウンロードするためのPython用のライブラリです。  

**警告！**  
このniconico_dlは開発が停止して、アップデートもこれからありません。  
代わりに[こちら](https://github.com/tasuren/niconico.py)を使用してください。

リファレンス：https://tasuren.github.io/niconico_dl/  
Github：https://github.com/tasuren/niconico_dl/

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

## Notes
もしDiscordのボイスチャットにニコニコ動画を流したい人は`NicoNicoVideoAsync.download`ではなく`NicoNicoVideoAsync.get_download_link`を使用して取得したダウンロードリンクで流すことを推奨します。  
`download`は動画をダウンロードするため時間がかかります。
なので`get_download_link`でダウンロードリンクを取得してそれを使い直接流すのを推奨します。  
注意：`close`をお忘れなく、詳細はリファレンスを見てください。
