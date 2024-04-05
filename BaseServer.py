# -*- coding: utf-8 -*-
"""

"""
import os
import webbrowser
from dotenv import load_dotenv
import threading


def open_browser():
    url = 'http://127.0.0.1:5000'
    webbrowser.open_new_tab(url)


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

from base import create_app

app = create_app('client')
threading.Timer(2, open_browser).start()
app.run()
