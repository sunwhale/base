# -*- coding: utf-8 -*-
"""

"""
import os

import webview
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

from base import create_app

app = create_app('development')


def resize(window):
    window.resize(1600, 1200)


if __name__ == "__main__":
    window = webview.create_window('固体力学与数值模拟', app, min_size=(800, 600))
    webview.start(resize, window, debug=False)
