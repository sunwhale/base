import requests
import re
import time
import pandas as pd

host = 'https://www.sunjingyu.com:8010'


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


def run_job(host, session, project_id, job_id):
    run_job_url = f'{host}/abaqus/run_job/{project_id}/{job_id}'
    run_job_response = session.get(run_job_url)
    if run_job_response.status_code == 200:
        print(f'run_job {project_id}-{job_id} success!')
        return True
    else:
        print(f'run_job {project_id}-{job_id} failed!')
        return False


def odb_to_npz(host, session, project_id, job_id):
    odb_to_npz_url = f'{host}/abaqus/odb_to_npz/{project_id}/{job_id}'
    odb_to_npz_response = session.get(odb_to_npz_url)
    if odb_to_npz_response.status_code == 200:
        print(f'odb_to_npz {project_id}-{job_id} success!')
        return True
    else:
        print(f'odb_to_npz {project_id}-{job_id} failed!')
        return False


def get_jobs_solver_status(host, session, project_id, job_ids):
    project_jobs_status = get_project_jobs_status(host, session, project_id)
    jobs_solver_status = []
    for job_id in job_ids:
        jobs_solver_status.append(project_jobs_status[job_id]['solver_status'])
    return jobs_solver_status


def get_jobs_odb_to_npz_status(host, session, project_id, job_ids):
    project_jobs_status = get_project_jobs_status(host, session, project_id)
    jobs_odb_to_npz_status = []
    for job_id in job_ids:
        jobs_odb_to_npz_status.append(project_jobs_status[job_id]['odb_to_npz_status'])
    return jobs_odb_to_npz_status


def set_job_parameter(host, session, project_id, job_id, parameter):
    view_job_url = f'{host}/abaqus/view_job/{project_id}/{job_id}'
    view_job_get_response = session.get(view_job_url)
    csrf_token = re.findall(r'<input.*?name="csrf_token".*?value="(.*?)".*?>', view_job_get_response.text)[0]
    data = {
        'para': parameter,
        'csrf_token': csrf_token
    }
    view_job_post_response = session.post(view_job_url, data=data)

    if view_job_post_response.status_code == 200:
        print(f'set_job_parameter {project_id}-{job_id} success!')
        return True
    else:
        print(f'set_job_parameter {project_id}-{job_id} failed!')
        return False


if __name__ == '__main__':
    session = login_session(host)
    project_id = 12
    job_ids = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    project_jobs_status = get_project_jobs_status(host, session, project_id)
    df = pd.read_excel('中能拉伸.xlsx', sheet_name='Sheet1')
    df.set_index('ID', inplace=True)

    is_set_parameter_success = True
    for job_id in job_ids:
        para = "*Parameter\n"
        for key in df.keys():
            para += f"{key} = {df.loc[job_id, key]}\n"

        if not set_job_parameter(host, session, project_id, job_id, para[:-1]):
            is_set_parameter_success = False

    is_run_job_success = True
    if is_set_parameter_success:
        for job_id in job_ids:
            if not run_job(host, session, project_id, job_id):
                is_run_job_success = False

    is_odb_to_npz_success = False
    if is_run_job_success:
        while True:
            jobs_solver_status = get_jobs_solver_status(host, session, project_id, job_ids)
            print(jobs_solver_status)
            if set(jobs_solver_status) == {'Completed'}:
                is_odb_to_npz_success = True
                for job_id in job_ids:
                    if not odb_to_npz(host, session, project_id, job_id):
                        is_odb_to_npz_success = False
            if is_odb_to_npz_success:
                break
            time.sleep(1)

    if is_odb_to_npz_success:
        while True:
            jobs_odb_to_npz_status = get_jobs_odb_to_npz_status(host, session, project_id, job_ids)
            print(jobs_odb_to_npz_status)
            if set(jobs_odb_to_npz_status) == {'Done'}:
                break
            time.sleep(1)
