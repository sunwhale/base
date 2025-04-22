import os.path

import requests
import re
import time
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.interpolate import interp1d

host = 'https://www.sunjingyu.com:8010'


def make_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


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


def get_job_file(host, session, project_id, job_id, filename, download_path):
    job_file_url = f'{host}/abaqus/get_job_file/{project_id}/{job_id}/{filename}'
    job_file_url_response = session.get(job_file_url)
    if job_file_url_response.status_code == 200:
        file_path = os.path.join(download_path, str(project_id), str(job_id))
        make_dir(file_path)
        with open(os.path.join(file_path, filename), 'wb') as f:
            f.write(job_file_url_response.content)
        return True
    else:
        return False


def get_specimen_file(host, session, experiment_id, specimen_id, filename, download_path):
    specimen_file_url = f'{host}/experiment/get_specimen_file/{experiment_id}/{specimen_id}/{filename}'
    specimen_file_url_response = session.get(specimen_file_url)
    if specimen_file_url_response.status_code == 200:
        file_path = os.path.join(download_path, str(experiment_id), str(specimen_id))
        make_dir(file_path)
        with open(os.path.join(file_path, filename), 'wb') as f:
            f.write(specimen_file_url_response.content)
        return True
    else:
        return False


def load_region_data(npz_file, regions):
    npz = np.load(npz_file, allow_pickle=True, encoding='latin1')
    data = npz['data'][()]
    time = npz['time']

    all_regions = data.keys()
    odb_data = {}
    out_data = {}

    for r in regions:

        odb_data[r] = {}
        region_elementLabels = []
        region_nodeLabels = []
        for e in data[r]['elements']:
            region_elementLabels.append(e['label'])
        for n in data[r]['nodes']:
            region_nodeLabels.append(n['label'])

        odb_data[r]['region_elementLabels'] = region_elementLabels
        odb_data[r]['region_nodeLabels'] = region_nodeLabels
        odb_data[r]['position'] = data[r]['fieldOutputs']['S']['position']
        odb_data[r]['regionType'] = data[r]['regionType']
        odb_data[r]['fieldOutputs'] = {}

        stress = np.array(data[r]['fieldOutputs']['S']['values'])
        try:
            strain = np.array(data[r]['fieldOutputs']['E']['values'])
        except:
            strain = np.array(data[r]['fieldOutputs']['LE']['values'])

        u = np.array(data[r]['fieldOutputs']['U']['values'])
        rf = np.array(data[r]['fieldOutputs']['RF']['values'])

        # print(u.shape)
        # print(rf.shape)

        out_data[r] = {}
        out_data[r]['time'] = time
        out_data[r]['disp'] = np.mean(u[:, :, 0], axis=1)
        out_data[r]['force'] = np.sum(rf[:, :, 0], axis=1)

    return out_data


def func(x: list, processed_tensile_data: dict, constants: dict):
    cost = 0.0
    cost += cal_tensile_cost(processed_tensile_data, x, constants)
    punish = 0.0
    y = cost
    for i in range(len(x)):
        punish += (max(0, -x[i])) ** 2
    y += 1e16 * punish
    print(y)
    return y


if __name__ == '__main__':
    # optimizations = [{'project_id': 48, 'job_id': 1, 'npz_name': 'Job-1.npz', 'experiments': [{'experiment_id': 3, 'specimen_id': 1, 'csv_name': 'timed.csv'}]},
    #                  {'project_id': 48, 'job_id': 2, 'npz_name': 'Job-1.npz', 'experiments': [{'experiment_id': 3, 'specimen_id': 4, 'csv_name': 'timed.csv'}]}]

    optimizations = [{'project_id': 48, 'job_id': 1, 'npz_name': 'Job-1.npz', 'experiments': [{'experiment_id': 3, 'specimen_id': 4, 'csv_name': 'timed.csv'}]}]

    exp_path = r'F:\Github\base\script\exp'
    sim_path = r'F:\Github\base\script\sim'

    is_exp_downloaded = True

    session = login_session(host)

    if not is_exp_downloaded:
        for optimization in optimizations:
            for experiment in optimization['experiments']:
                print(get_specimen_file(host, session, experiment['experiment_id'], experiment['specimen_id'], experiment['csv_name'], exp_path))

    paras_0 = [10, 1, 1]
    constants = {'E_inf': 1.0,
                 'nu': 0.14,
                 'mode': 'analytical',
                 'tau_count': 3,
                 'tau': [0.1, 2.0, 1000.0],
                 'E': [4.37822768, 3.52537335, 0.71464186],
                 'lc': 1.0}

    is_set_parameter_success = True
    for optimization in optimizations:
        para = f"""*Parameter
        Time = 1.4
        E = 1.0
        g_1 = 0.1
        g_2 = 0.63
        g_3 = 0.12
        k_1 = 0.1
        k_2 = 0.1
        k_3 = 0.1
        Tau_1 = 0.05
        Tau_2 = 1.0
        Tau_3 = 100.0""".replace(' ', '')

        if not set_job_parameter(host, session, optimization['project_id'], optimization['job_id'], para[:-1]):
            is_set_parameter_success = False

    is_run_job_success = True
    if is_set_parameter_success:
        for optimization in optimizations:
            if not run_job(host, session, optimization['project_id'], optimization['job_id']):
                is_run_job_success = False

    is_odb_to_npz_success = False
    if is_run_job_success:
        while True:
            jobs_solver_status = []
            for optimization in optimizations:
                jobs_solver_status += get_jobs_solver_status(host, session, optimization['project_id'], [optimization['job_id']])
            print(jobs_solver_status)
            if set(jobs_solver_status) == {'Completed'}:
                is_odb_to_npz_success = True
                for optimization in optimizations:
                    if not odb_to_npz(host, session, optimization['project_id'], optimization['job_id']):
                        is_odb_to_npz_success = False
            if is_odb_to_npz_success:
                break
            time.sleep(1)

    is_odb_to_npz_done = False
    if is_odb_to_npz_success:
        while True:
            jobs_odb_to_npz_status = []
            for optimization in optimizations:
                jobs_odb_to_npz_status += get_jobs_odb_to_npz_status(host, session, optimization['project_id'], [optimization['job_id']])
            print(jobs_odb_to_npz_status)
            if set(jobs_odb_to_npz_status) == {'Done'}:
                is_odb_to_npz_done = True
                break
            time.sleep(1)

    is_npz_download = True
    if is_odb_to_npz_done:
        while True:
            for optimization in optimizations:
                if not get_job_file(host, session, optimization['project_id'], optimization['job_id'], optimization['npz_name'], sim_path):
                    is_npz_download = False
            if is_npz_download:
                break
            time.sleep(1)

    sim_data = {}
    for i, optimization in enumerate(optimizations):
        npz_file = os.path.join(sim_path, str(optimization['project_id']), str(optimization['job_id']), optimization['npz_name'])
        try:
            sim_data[i] = load_region_data(npz_file, ['PART-1-1.SET-X1'])
        except:
            print('error:' + npz_file)

    for sim_id in sim_data.keys():
        strain_fem = sim_data[sim_id]['PART-1-1.SET-X1']['disp'] / 1.0
        stress_fem = sim_data[sim_id]['PART-1-1.SET-X1']['force'] / 1.0
        sim_data[sim_id]['PART-1-1.SET-X1']['f'] = interp1d(strain_fem, stress_fem, kind='linear')
        plt.plot(strain_fem, stress_fem, marker='*', label="fem%s" % sim_id)

    exp_data = {}

    cost = 0.0
    for i, optimization in enumerate(optimizations):
        f = sim_data[i]['PART-1-1.SET-X1']['f']
        for experiment in optimization['experiments']:
            experiment_id = experiment['experiment_id']
            specimen_id = experiment['specimen_id']
            csv_file = os.path.join(exp_path, str(experiment['experiment_id']), str(experiment['specimen_id']), experiment['csv_name'])
            try:
                df = pd.read_csv(csv_file)
                exp_data[f'{experiment_id}-{specimen_id}'] = df
                strain_exp = df['Strain'].to_numpy()
                stress_exp = df['Stress_MPa'].to_numpy()
                condition = strain_exp < 0.1
                strain_exp = strain_exp[condition]
                stress_exp = stress_exp[condition]
                stress_sim = f(strain_exp)
                cost += np.sum(((stress_exp - stress_sim) / max(stress_exp)) ** 2, axis=0) / len(stress_exp)
            except Exception as e:
                print('error:' + csv_file)

    for key in exp_data.keys():
        strain = exp_data[key]['Strain']
        stress = exp_data[key]['Stress_MPa']
        plt.plot(strain, stress, marker='o', label=f'Exp. {key}')

    plt.xlabel('Strain')
    plt.ylabel('Stress, MPa')
    plt.legend(loc='upper right')
    plt.show()
