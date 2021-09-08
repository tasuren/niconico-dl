
from niconico_dl import __version__, __author__
from setuptools import setup
from os.path import exists


if exists("readme.md"):
    with open("readme.md", "r") as f:
        long_description = f.read()
else:
    long_description = "..."


if exists("requirements.txt"):
    with open("requirements.txt", "r") as f:
        requires = f.read().splitlines()
else:
    requires = []


setup(
    name='niconico_dl',
    version=__version__,
    description='ニコニコ動画ダウンローダー NicoNico Video Downloader',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://tasuren.github.io/niconico_dl/',
    author=__author__,
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
    install_requires=requires,
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ]
)
