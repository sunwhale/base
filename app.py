# -*- coding: utf-8 -*-
"""

"""
import os

import webview
import webview.menu as wm
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

from base import create_app

app = create_app('production')


def resize(window):
    window.resize(1600, 1200)


def return_to_main():
    active_window = webview.active_window()
    if active_window:
        active_window.load_url('/')


def show_help():
    active_window = webview.active_window()
    if active_window:
        active_window.create_confirmation_dialog('关于base', '当前版本：0.1.4\n作者：孙经雨')


if __name__ == "__main__":

    menu_items = [
        wm.Menu(
            '文件',
            [
                wm.MenuAction('返回主界面', return_to_main),
                wm.MenuSeparator(),
            ]
        ),
        wm.Menu(
            '帮助',
            [
                wm.MenuAction('关于base', show_help)
            ]
        )
    ]

    window = webview.create_window('固体力学与数值模拟', app, min_size=(800, 600))
    webview.start(resize, window, debug=False, menu=menu_items)
