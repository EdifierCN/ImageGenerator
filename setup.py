from setuptools import setup

APP = ['./main.py']
DATA_FILES = []
OPTIONS = {'optimize': 2, 'excludes': ['packaging', 'wx.lib.agw'], 'iconfile': 'app.icns', 'plist': {
    'CFBundleName': "图片生成器",
    'CFBundleDisplayName': "Image Generator",
    'CFBundleIconFile': "app.icns",
    'LSMinimumSystemVersion': '14.0.0',
}}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    install_requires=[
        'setuptools',
        'jaraco.text',
    ]
)
