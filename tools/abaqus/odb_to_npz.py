# -*- coding: utf-8 -*-
"""
读取odb文件，输出npz格式数据文件
"""
from abaqusConstants import *
from odbAccess import *
import json
import os
import numpy as np

position = {
    'INTEGRATION_POINT': INTEGRATION_POINT,
    'NODAL': NODAL,
    'ELEMENT_NODAL': ELEMENT_NODAL,
    'CENTROID': CENTROID
}


def dump_json(file_name, data):
    """
    Write JSON data to file.
    """
    with open(file_name, 'w') as f:
        return json.dump(data, f)


def load_json(file_name):
    """
    Read JSON data from file.
    """
    with open(file_name, 'r') as f:
        return json.load(f)


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        pass
    return False


def is_write(n, total, seg=100):
    if total < seg:
        return True
    else:
        a = int(total/seg)
        if n%a == 0:
            return True
        if n == total:
            return True
        return False    
    

def odb_to_npz(setting_file):

    f_proc = open('.odb_to_npz_proc', 'w')
    with open('.odb_to_npz_status', 'w') as f:
        f.write('Running')

    # Read settings from the setting file
    settings = load_json(setting_file)
    odbs = settings['ODB']
    regions = settings['Regions']
    variables = settings['Variables']
    step_frames = settings['Frames']

    total_count = 0
    # loop of odbs
    for odb_name in odbs:
        # loop of regions
        for r in regions:
            # loop of steps
            for step in step_frames:
                total_count += len(step[1])
                if step[1] == []:
                    odb = openOdb(path=str(odb_name), readOnly=True)
                    total_count += len(odb.steps[str(step[0])].frames)
                    odb.close()

    current_count = 0
    # loop of odbs
    for odb_name in odbs:
        try:
            odb = openOdb(path=str(odb_name), readOnly=True)
            data = {}
            time = []

            # loop of regions
            for r in regions:
                r_name = str(r[0])
                r_type = str(r[1])

                data[r_name] = {
                    'fieldOutputs': {},
                    'regionType': r_type,
                    'elements': [],
                    'nodes': [],
                }

                if r_type == "Element set":
                    if '.' in r_name:
                        instanceName = r_name.split('.')[0]
                        setName = r_name.split('.')[1]
                        region = odb.rootAssembly.instances[instanceName].elementSets[setName]
                        for e in region.elements:
                            element = {
                                'label': e.label,
                                'type': e.type,
                                'connectivity': e.connectivity,
                                'instanceName': e.instanceName
                            }
                            data[r_name]['elements'].append(element)
                    else:
                        region = odb.rootAssembly.elementSets[r_name]
                        for e in region.elements[0]:
                            element = {
                                'label': e.label,
                                'type': e.type,
                                'connectivity': e.connectivity,
                                'instanceName': e.instanceName
                            }
                            data[r_name]['elements'].append(element)

                if r_type == "Node set":
                    if '.' in r_name:
                        instanceName = r_name.split('.')[0]
                        setName = r_name.split('.')[1]
                        region = odb.rootAssembly.instances[instanceName].nodeSets[setName]
                        for n in region.nodes:
                            node = {
                                'label': n.label,
                                'coordinates': n.coordinates,
                                'instanceName': n.instanceName
                            }
                            data[r_name]['nodes'].append(node)
                    else:
                        region = odb.rootAssembly.nodeSets[r_name]
                        for n in region.nodes[0]:
                            node = {
                                'label': n.label,
                                'coordinates': n.coordinates,
                                'instanceName': n.instanceName
                            }
                            data[r_name]['nodes'].append(node)

                if r_type == "Instance":
                    region = odb.rootAssembly.instances[r_name]
                    for e in region.elements:
                        element = {
                            'label': e.label,
                            'type': e.type,
                            'connectivity': e.connectivity,
                            'instanceName': e.instanceName
                        }
                        data[r_name]['elements'].append(element)
                    for n in region.nodes:
                        node = {
                            'label': n.label,
                            'coordinates': n.coordinates,
                            'instanceName': n.instanceName
                        }
                        data[r_name]['nodes'].append(node)

                for v in variables:
                    v_name = str(v[0])
                    v_position = str(v[1])
                    data[r_name]['fieldOutputs'][v_name] = {
                        'position': v_position,
                        'baseElementType': [],
                        'componentLabels': [],
                        'values': [],
                        'elementLabels': [],
                        'nodeLabels': []
                    }

                # loop of steps
                time = []
                for step in step_frames:
                    step_name = str(step[0])
                    frames_in_step = step[1]
                    frames = odb.steps[step_name].frames

                    # loop of frames
                    if frames_in_step == []:
                        frames_in_step = range(len(frames))

                    if float(len(frames_in_step))/len(frames) > 0.1:
                        for i, frame in enumerate(frames):
                            if i in frames_in_step:
                                time.append(frame.frameValue)
                                current_count += 1
                                if is_write(current_count, total_count):
                                    f_proc.write('%.1f\n' % (float(current_count)*100/total_count))
                                    f_proc.flush()
                                # loop of variables
                                for v in variables:
                                    v_name = str(v[0])
                                    v_position = str(v[1])
                                    field_output = frame.fieldOutputs[v_name].getSubset(position=position[v_position], region=region)
                                    if len(field_output.bulkDataBlocks) > 0:
                                        bulk_data = field_output.bulkDataBlocks[0]
                                        field_var = data[r_name]['fieldOutputs'][v_name]
                                        field_var['values'].append(np.array(bulk_data.data))
                                        if field_var['elementLabels'] == []:
                                            field_var['elementLabels'].append(np.array(bulk_data.elementLabels))
                                            field_var['nodeLabels'].append(np.array(bulk_data.nodeLabels))
                                            field_var['baseElementType'].append(np.array(bulk_data.baseElementType))
                                            field_var['componentLabels'].append(np.array(bulk_data.componentLabels))

                    else:
                        for frame_id in frames_in_step:
                            print(frame_id)
                            time.append(frames[frame_id].frameValue)
                            current_count += 1
                            if is_write(current_count, total_count):
                                f_proc.write('%.1f\n' % (float(current_count)*100/total_count))
                                f_proc.flush()
                            # loop of variables
                            for v in variables:
                                v_name = str(v[0])
                                v_position = str(v[1])
                                field_output = frames[frame_id].fieldOutputs[v_name].getSubset(position=position[v_position], region=region)
                                if len(field_output.bulkDataBlocks) > 0:
                                    bulk_data = field_output.bulkDataBlocks[0]
                                    field_var = data[r_name]['fieldOutputs'][v_name]
                                    field_var['values'].append(np.array(bulk_data.data))
                                    if field_var['elementLabels'] == []:
                                        field_var['elementLabels'].append(np.array(bulk_data.elementLabels))
                                        field_var['nodeLabels'].append(np.array(bulk_data.nodeLabels))
                                        field_var['baseElementType'].append(np.array(bulk_data.baseElementType))
                                        field_var['componentLabels'].append(np.array(bulk_data.componentLabels))

            np.savez(odb_name.replace('.odb', '') + '.npz',
                     data=data,
                     time=time)

            del data
            del time

            odb.close()
            with open('.odb_to_npz_status', 'w') as f:
                f.write('Done')

        except OdbError, e:
            print('OdbError: %s\n' % str(e))
            with open('.odb_to_npz_status', 'w') as f:
                f.write('Error')
        except KeyError, e:
            print('KeyError: %s\n' % str(e))
            with open('.odb_to_npz_status', 'w') as f:
                f.write('Error')
        except:
            print('Unknown Error\n')
            with open('.odb_to_npz_status', 'w') as f:
                f.write('Error')

    f_proc.close()

if __name__ == '__main__':
    setting_file = sys.argv[-1]
    odb_to_npz(setting_file)
