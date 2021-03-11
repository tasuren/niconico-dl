# niconico_dl / ニコニコ_dl
ニコニコ動画の動画をダウンロードすることができるPythonモジュールです。  
使用は自己責任で違法な用途には使用しないでください。  
そしてサーバーに負荷がかからない程度で、使用してください。  
`pip install niconico-dl`  

# Example / 例
sm9720246の部分はIDで動画のURLの最後の部分です。  
## ダウンロード
```python
from niconico_dl import NicoNico


niconico = NicoNico("sm9720246")
# その他引数でlog=Falseがあり、Trueにすると進行状況が出力されます。

title = niconico.data["video"]["title"]
print(title)
# 【東方合同動画企画】魔理沙とアリスのクッキーKiss

niconico.download(title + ".mp4")
# その他引数：timeout=5,chunk_size=1024


niconico.close()
# 最後にはこれを置く。 それかniconicoに別のものを入れる。
```
## ダウンロードリンクの取得
```python
from niconico_dl import NicoNico


niconico = NicoNico("sm9720246")

title = niconico.data["video"]["title"]
print(title)
# 【東方合同動画企画】魔理沙とアリスのクッキーKiss

url = niconico.get_download_link()
print(url)
# https://pf0155780d7.dmc.nico/vod/ht2_nicovideo/nicovideo-sm9720246_3b0afad5f792d95ff576d66ed955614fdff9e58b648b3b3d83006a0533ef90b9?ht2_nicovideo=86146818.oufj1q6yp7_qpr6wt_3e436vz3cjqri


niconico.close()
# 最後にはこれを置く。 それかniconicoに別のものを入れる。
# ※URLを使い終わったら実行をしないとURLが無効になります。
```
# 非同期版
`pip install niconico-dl-async`  
```python
from asyncio import get_event_loop
from niconico_dl_async import NicoNico


async def download(nicoid):

	niconico = NicoNico(nicoid)
	# その他引数でlog=Falseがあり、Trueにすると進行状況が出力されます。

	data = await niconico.get_info()
	title = data["video"]["title"]
	print(title)
	# 【東方合同動画企画】魔理沙とアリスのクッキーKiss

	await niconico.download(title + ".mp4")
	# その他引数：timeout=5,chunk_size=1024
	url = await niconico.get_download_link()
	# 注意：closeをしてしばらくするとURLは使えなくなります。

	niconico.close()
	# 最後にはこれを置く。 それかniconicoに別のものを入れる。


get_event_loop().run_until_complete(download("sm9720246"))
```
