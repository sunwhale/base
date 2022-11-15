# -*- coding: utf-8 -*-
"""
读取npz文件并进行分析
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import originpro as op
import requests


def load_region_data(npz_file, regions):

    npz = np.load(npz_file, allow_pickle=True, encoding='latin1')
    data = npz['data'][()]
    time = npz['time']

    all_regions = data.keys()
    odb_data = {}

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

        # sdv1 = np.array(data[r]['fieldOutputs']['SDV1']['values'])
        # sdv3 = np.array(data[r]['fieldOutputs']['SDV3']['values'])
        # sdv19 = np.array(data[r]['fieldOutputs']['SDV19']['values'])
        # sdv21 = np.array(data[r]['fieldOutputs']['SDV21']['values'])
        # sdv22 = np.array(data[r]['fieldOutputs']['SDV22']['values'])
        # sdv23 = np.array(data[r]['fieldOutputs']['SDV23']['values'])
        # sdv24 = np.array(data[r]['fieldOutputs']['SDV24']['values'])
        sdv121 = np.array(data[r]['fieldOutputs']['SDV121']['values'])

        # print(stress.shape)
        # print(strain.shape)

    e_sim = strain[:, 0, 1]
    s_sim = stress[:, 0, 1]
    d_sim = sdv1[:, 0, 0]
    delta_sim = sdv3[:, 0, 0]
    pacm = sdv19[:, 0, 0]
    dp_sim = sdv21[:, 0, 0]
    ds_sim = sdv22[:, 0, 0]
    df_sim = sdv23[:, 0, 0]
    delta0_sim = sdv24[:, 0, 0]

    data = {}
    data['time'] = time
    data['delta_sim'] = delta_sim
    data['delta0_sim'] = delta0_sim
    data['d_sim'] = d_sim
    data['dp_sim'] = dp_sim
    data['ds_sim'] = ds_sim
    data['df_sim'] = df_sim
    data['pacm'] = pacm
    data['strain'] = e_sim
    data['stress'] = s_sim

    return data


def load_status(url='http://127.0.0.1:5000/'):
    response = requests.get(url)
    result = response.json()
    jobs = result['data']
    jobs_status = {}
    for job in jobs:
        job_id = job['job_id']
        jobs_status[job_id] = {}
        for key in job.keys():
            jobs_status[job_id][key] = job[key]
    return jobs_status


if __name__ == '__main__':
    data = {}

    jobs_status = load_status(
        'http://127.0.0.1:5000/abaqus/project_jobs_status/3')

    job_ids = [1, 2]

    for job_id in job_ids:
        job_status = jobs_status[job_id]
        job_path = job_status['path']
        npz_file = os.path.join(job_path, job_status['job'] + '.npz')
        try:
            data[job_id] = load_region_data(npz_file,
                                            ['PART-1-1.GRAIN_1'])
        except:
            print('error:' + npz_file)

    for job_id in data.keys():
        # plt.plot(data[job_id]['strain'],
        #          data[job_id]['stress'],
        #          label=jobs_status[job_id]['period'])
        plt.plot(data[job_id]['time']*float(jobs_status[job_id]['amp']),
                 data[job_id]['pacm'],
                 label=jobs_status[job_id]['period'])
    
    plt.legend(loc=0, frameon=1)
    # plt.xscale('log')
    # plt.yscale('log')
    # plt.xlim(1e6,2e9)
    # plt.savefig('%s.png' % job_id, dpi=150, transparent=False)
    # plt.close()
