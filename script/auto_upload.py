import os
import re
import time

import requests
from tqdm import tqdm

# host = 'https://www.sunjingyu.com:8010'


host = 'http://127.0.0.1:5000'


def login_session(host):
    # 创建一个 Session 对象
    session = requests.Session()

    # 先请求登录页面获取 csrf_token
    login_url = host + '/auth/login'
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
        return session
    else:
        print("Login failed.")
        raise NotImplementedError


def get_project_jobs_status(host, session, project_id):
    project_jobs_status_url = f'{host}/abaqus/project_jobs_status/{project_id}'
    project_jobs_status_response = session.get(project_jobs_status_url)
    project_jobs_status = {}
    if project_jobs_status_response.status_code == 200:
        status = project_jobs_status_response.json()
        for data in status['data']:
            project_jobs_status[data['job_id']] = data
        return project_jobs_status
    else:
        return project_jobs_status


def get_jobs_prescan_odb_status(host, session, project_id, job_ids):
    project_jobs_status = get_project_jobs_status(host, session, project_id)
    jobs_prescan_odb_status = []
    for job_id in job_ids:
        jobs_prescan_odb_status.append(project_jobs_status[job_id]['prescan_status'])
    return jobs_prescan_odb_status


def upload_file(host, session, project_id, job_id, filepath):
    upload_url = host + f'/abaqus/upload_job_file/{project_id}/{job_id}'
    upload_page = session.get(upload_url)
    csrf_token = re.findall(r'<input.*?name="csrf_token".*?value="(.*?)".*?>', upload_page.text)[0]
    data = {
        'csrf_token': csrf_token,
    }
    files = {'filename': open(filepath, 'rb')}
    print(data)
    upload_response = session.post(upload_url, data=data, files=files)
    if upload_response.status_code == 200:
        print(f'Upload {filepath} to {project_id}-{job_id} success!')
        return True
    else:
        print(f'Upload {filepath} to {project_id}-{job_id} failed!')
        return False


if __name__ == '__main__':
    session = login_session(host)

    project_id = 1
    job_id = 1
    filepath = '中能拉伸.csv'

    upload_file(host, session, project_id, job_id, filepath)
