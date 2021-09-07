# niconico_dl - Main

from niconico_dl import NicoNicoVideo
from sys import argv


args = [
    arg for arg in argv
    if not arg.startswith(
        ("py", "-m")
    ) and "niconico_dl" not in arg
]
HELP = """# niconico_dl
ニコニコ動画にある動画をmp4形式ダウンロードします。
使用方法：`niconico_dl [URL]`
ダウンロードした動画は`output.mp4`という名前で実行したディレクトリに保存されます。"""


def main():
    if args and args[0]:
        with NicoNicoVideo(args[0], log=True) as nico:
            nico.download("output.mp4")
    else:
        print(HELP)


if __name__ == "__main__":
    main()