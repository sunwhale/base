import os
import re
import time

import requests
from tqdm import tqdm

host = 'https://www.sunjingyu.com:8010'


# host = 'http://127.0.0.1:5000'


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


def prescan_odb(host, session, project_id, job_id):
    prescan_odb_url = f'{host}/abaqus/prescan_odb/{project_id}/{job_id}'
    prescan_odb_response = session.get(prescan_odb_url)
    if prescan_odb_response.status_code == 200:
        print(f'prescan_odb {project_id}-{job_id} success!')
        return True
    else:
        print(f'prescan_odb {project_id}-{job_id} failed!')
        return False


def print_figure(host, session, project_id, job_id):
    print_figure_url = f'{host}/abaqus/print_figure/{project_id}/{job_id}'

    # 先请求页面获取 csrf_token
    print_figure_page = session.get(print_figure_url)
    csrf_token = re.findall(r'<input.*?name="csrf_token".*?value="(.*?)".*?>', print_figure_page.text)[0]

    # 使用获取到的 csrf_token 提交表单
    data = {
        'width': '200.0',
        'height': '400.0',
        'imageSize': '(200, 400)',
        'legend': 'OFF',
        'legendPosition': '(2, 98)',
        'triad': 'OFF',
        'projection': 'PARALLEL',
        'views': 'Front',
        'plotState': '(DEFORMED,)',
        # 'plotState': '(CONTOURS_ON_DEF,)',
        'uniformScaleFactor': '1.0',
        'step': 'Step-1',
        'frame': '-1',
        'variableLabel': 'NT11',
        'refinement': '()',
        'outputPosition': 'NODAL',
        'visibleEdges': 'FREE',
        'maxAutoCompute': 'ON',
        'maxValue': '1.0',
        'minAutoCompute': 'ON',
        'minValue': '0.0',
        'colorMappings': 'Set',
        'mirrorAboutXyPlane': 'False',
        'mirrorAboutXzPlane': 'False',
        'mirrorAboutYzPlane': 'False',
        'removeElementSet': '',
        'replaceElementSet': '',
        'useStatus': 'True',
        'statusLabel': 'NT11',
        'statusPosition': 'NODAL',
        'statusRefinement': '()',
        'statusMinimum': '0.8',
        'statusMaximum': '1.0',
        'animate': 'ON',
        'frameInterval': '2',
        'startFrame': '0',
        'endFrame': '-1',
        'fps': '12',
        'csrf_token': csrf_token
    }
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


if __name__ == '__main__':
    session = login_session(host)
    project_id = 29
    job_ids = range(1, 65)
    project_jobs_status = get_project_jobs_status(host, session, project_id)

    # is_prescan_odb_success = True
    # for job_id in job_ids:
    #     if not prescan_odb(host, session, project_id, job_id):
    #         is_prescan_odb_success = False

    # if is_prescan_odb_success:
    #     while True:
    #         jobs_odb_to_npz_status = get_jobs_prescan_odb_status(host, session, project_id, job_ids)
    #         print(jobs_odb_to_npz_status)
    #
    #         if set(jobs_odb_to_npz_status) == {'Done'}:
    #             break
    #         time.sleep(1)

    for job_id in job_ids:
        print_figure(host, session, project_id, job_id)

    # for job_id in job_ids:
    #     print_figure_gif(host, session, project_id, job_id, 'NT11')

    for job_id in job_ids:
        print_figure_gif(host, session, project_id, job_id, 'DEFORMED_Set')

    variable = 'DEFORMED_Set'
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    for job_id in job_ids:
        file_url = f'{host}/abaqus/get_job_file/{project_id}/{job_id}/{variable}.gif'
        destination = os.path.join('downloads', f'{project_id}-{job_id}-{variable}.gif')
        get_job_file(session, file_url, destination)
