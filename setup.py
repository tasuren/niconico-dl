
from setuptools import setup
from os.path import exists


if exists("readme.md"):
    with open("readme.md", "r") as f:
        long_description = f.read()
else:
    long_description = "..."


with open("niconico_dl/__init__.py", "r") as f:
    text = f.read()
    version = text.split('__version__ = "')[1].split('"')[0]
    author = text.split('__author__ = "')[1].split('"')[0]


setup(
    name='niconico_dl',
    version=version,
    description='ニコニコ動画ダウンローダー NicoNico Video Downloader',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://tasuren.github.io/niconico_dl/',
    author=author,
    author_email='tasuren5@gmail.com',
    license='MIT',
    keywords='niconico video download',
    packages=[
        "niconico_dl"
    ],
    entry_points={
        "console_scripts": [
            "niconico_dl = niconico_dl.__main__:main"
        ]
    },
    install_requires=["aiofiles", "aiohttp", "requests", "bs4"],
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ]
)
