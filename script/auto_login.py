# -*- coding: utf-8 -*-
"""

"""
import requests
import re

# 创建一个 Session 对象
session = requests.Session()

# 先请求登录页面获取 csrf_token
login_url = 'http://127.0.0.1:5000/auth/login'
login_page = session.get(login_url)
csrf_token = re.findall(r'<input.*?name="csrf_token".*?value="(.*?)".*?>', login_page.text)[0]

# 使用获取到的 csrf_token 登录
data = {
    'email': 'manager@manager.com',
    'password': 'solidmechanics666666',
    'csrf_token': csrf_token
}
login_response = session.post(login_url, data=data)

# 检查登录是否成功
if login_response.status_code == 200:
    print("Login successful!")
else:
    print("Login failed.")

# 在后续的请求中使用登录后的cookies
response = session.get('http://127.0.0.1:5000/abaqus/job_status/1/1')

# 检查访问受保护页面的响应
if response.status_code == 200:
    print(response.text)
else:
    print("Failed to access protected page.")