# -*- coding: utf-8 -*-
"""

"""
import ctypes
import os
import sys
import threading
import webbrowser

from dotenv import load_dotenv


def open_browser():
    url = 'http://127.0.0.1:5000'
    webbrowser.open_new_tab(url)


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

from base import create_app

if not is_admin():
    # 这段代码会检查当前用户是否为管理员，如果不是管理员，则使用 ShellExecuteW 函数以管理员权限重新启动脚本，并退出当前进程。
    # 请注意，这种方法只适用于 Windows 系统。
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
    sys.exit()
else:
    app = create_app('client')
    threading.Timer(2, open_browser).start()
    app.run()
