import json
import os
import re
import time
from datetime import datetime

import requests
from tqdm import tqdm

host = 'https://www.sunjingyu.com:8010'
host = 'http://127.0.0.1:5000'


# host = 'http://127.0.0.1:5000'
def load_json(file_path, encoding='utf-8'):
    """
    Read JSON data from file.
    """
    with open(file_path, 'r') as f:
        return json.load(f)


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


def get_job_status(host, session, project_id, job_id):
    job_status_url = f'{host}/abaqus/job_status/{project_id}/{job_id}'
    job_status_response = session.get(job_status_url)
    if job_status_response.status_code == 200:
        return job_status_response.json()
    else:
        return {}


def get_jobs_prescan_odb_status(host, session, project_id, job_ids):
    project_jobs_status = get_project_jobs_status(host, session, project_id)
    jobs_prescan_odb_status = []
    for job_id in job_ids:
        jobs_prescan_odb_status.append(project_jobs_status[job_id]['prescan_status'])
    return jobs_prescan_odb_status


def prescan_odb(host, session, project_id, job_id):
    prescan_odb_url = f'{host}/abaqus/prescan_odb/{project_id}/{job_id}'
    prescan_odb_response = session.get(prescan_odb_url)
    if prescan_odb_response.status_code == 200:
        print(f'prescan_odb {project_id}-{job_id} success!')
        return True
    else:
        print(f'prescan_odb {project_id}-{job_id} failed!')
        return False


def print_figure(host, session, project_id, job_id, data):
    print_figure_url = f'{host}/abaqus/print_figure/{project_id}/{job_id}'

    # 先请求页面获取 csrf_token
    print_figure_page = session.get(print_figure_url)
    csrf_token = re.findall(r'<input.*?name="csrf_token".*?value="(.*?)".*?>', print_figure_page.text)[0]

    # 使用获取到的 csrf_token 提交表单
    data['csrf_token'] = csrf_token
    print_figure_response = session.post(print_figure_url, data=data)

    # 检查登录是否成功
    if print_figure_response.status_code == 200:
        print(f'Print figure {project_id}-{job_id} successful!')
        return session
    else:
        print(f'Print figure {project_id}-{job_id} failed.')
        raise NotImplementedError


def print_figure_gif(host, session, project_id, job_id, variable):
    print_figure_gif_url = f'{host}/abaqus/print_figure_gif/{project_id}/{job_id}/{variable}'
    print_figure_gif_response = session.get(print_figure_gif_url)
    time.sleep(1)
    if print_figure_gif_response.status_code == 200:
        print(f'Create gif {project_id}-{job_id} success!')
        return True
    else:
        print(f'Create gif {project_id}-{job_id} failed!')
        return False


def get_job_file(session, url, destination):
    response = session.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))

    print(url)
    # 使用 tqdm 显示下载进度条
    progress_bar = tqdm(total=total_size, unit='B', unit_scale=True)

    with open(destination, 'wb') as file:
        for data in response.iter_content(chunk_size=1024):
            progress_bar.update(len(data))
            file.write(data)

    progress_bar.close()


def filter_later_than(data, given_time_str):
    """
    返回 time 字段晚于 given_time_str 的数据项
    """
    given_time = datetime.strptime(given_time_str, '%Y-%m-%d %H:%M:%S')
    result = []
    for item in data:
        item_time = datetime.strptime(item['time'], '%Y-%m-%d %H:%M:%S')
        if item_time > given_time:
            result.append(item)
    return result


if __name__ == '__main__':
    if not os.path.exists('../downloads'):
        os.makedirs('../downloads')

    session = login_session(host)
    project_id = 70
    job_ids = [14]
    project_jobs_status = get_project_jobs_status(host, session, project_id)

    for job_id in job_ids:
        for i in [23]:
            data = load_json(f'print_figure_{i}.json')
            given_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print_figure(host, session, project_id, job_id, data)
            time.sleep(2)
            job_status = get_job_status(host, session, project_id, 13)
            png_items = [item for item in job_status['files'] if item['name'].lower().endswith('.png')]
            print(given_time_str)
            download_png_items = filter_later_than(png_items, given_time_str)

            for download_png_item in download_png_items:
                png_name = download_png_item['name']
                file_url = f'{host}/abaqus/get_job_file/{project_id}/{job_id}/{png_name}'
                destination = os.path.join('../downloads', f'{project_id}-{job_id}-{png_name}')
                get_job_file(session, file_url, destination)


    # for job_id in job_ids:
    #     data = load_json(f'print_figure_template_1.json')
    #
    #     # for element_set in ['BLOCK-1-1.SET-CELL-GRAIN', 'BLOCK-2-1.SET-CELL-GRAIN', 'BLOCK-11-1.SET-CELL-GRAIN', 'BLOCK-12-1.SET-CELL-GRAIN']:
    #     for element_set in ['BLOCK-1-1.SET-CELL-INSULATION', 'BLOCK-2-1.SET-CELL-INSULATION', 'BLOCK-11-1.SET-CELL-INSULATION', 'BLOCK-12-1.SET-CELL-INSULATION']:
    #     # for element_set in ['BLOCK-1-1.SET-CELL-GLUE-A', 'BLOCK-2-1.SET-CELL-GLUE-A', 'BLOCK-11-1.SET-CELL-GLUE-A', 'BLOCK-12-1.SET-CELL-GLUE-A']:
    #     # for element_set in ['BLOCK-1-1.SET-CELL-GLUE-B', 'BLOCK-2-1.SET-CELL-GLUE-B', 'BLOCK-11-1.SET-CELL-GLUE-B', 'BLOCK-12-1.SET-CELL-GLUE-B']:
    #
    #         data['replaceElementSet'] = element_set
    #
    #         given_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #         print_figure(host, session, project_id, job_id, data)
    #         time.sleep(2)
    #         job_status = get_job_status(host, session, project_id, 13)
    #         png_items = [item for item in job_status['files'] if item['name'].lower().endswith('.png')]
    #         print(given_time_str)
    #         download_png_items = filter_later_than(png_items, given_time_str)
    #         print(download_png_items)
    #
    #         for download_png_item in download_png_items:
    #             png_name = download_png_item['name']
    #             file_url = f'{host}/abaqus/get_job_file/{project_id}/{job_id}/{png_name}'
    #             destination = os.path.join('downloads', f'{project_id}-{job_id}-{png_name}')
    #             get_job_file(session, file_url, destination)