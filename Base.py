# -*- coding: utf-8 -*-
"""

"""
import ctypes
import os
import sys

import pyautogui
import webview
import webview.menu as wm
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

from base import create_app

app = create_app('client')


def resize(window):
    w, h = pyautogui.size()
    window.resize(w, int(h * 0.96))
    window.move(0, 0)


def return_to_main():
    active_window = webview.active_window()
    if active_window:
        active_window.load_url('/')


def open_viewer():
    active_window = webview.active_window()
    if active_window:
        active_window.load_url('/viewer')


def show_help():
    active_window = webview.active_window()
    if active_window:
        active_window.create_confirmation_dialog('关于 Base', '程序版本：0.1.5\nJingyu Sun © 2020-2023')


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


if __name__ == "__main__":

    if not is_admin():
        # 这段代码会检查当前用户是否为管理员，如果不是管理员，则使用 ShellExecuteW 函数以管理员权限重新启动脚本，并退出当前进程。
        # 请注意，这种方法只适用于 Windows 系统。
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
        sys.exit()

    # 需要 python >= 3.10 否则添加菜单时会报错
    menu_items = [
        wm.MenuAction('主界面', return_to_main),
        wm.Menu(
            '帮助',
            [
                wm.MenuAction('关于base', show_help),
                # wm.MenuSeparator(),
            ]
        )
    ]

    window = webview.create_window('固体力学与数值模拟', app, min_size=(800, 600), text_select=True)
    webview.start(resize, window, debug=bool(os.environ.get('WEBVIEW_DEBUG')), menu=menu_items)
