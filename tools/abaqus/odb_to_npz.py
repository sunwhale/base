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


def odb_to_npz(setting_file):
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
                # loop of frames
                for frame_id in step[1]:
                    total_count += 1

    print(total_count)

    # loop of odbs
    for odb_name in odbs:
        odb = openOdb(path=str(odb_name), readOnly=True)
        data = {}
        time = []
        print(odb_name)
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
                    try:
                        region = odb.rootAssembly.instances[instanceName].elementSets[setName]
                        for e in region.elements:
                            element = {
                                'label': e.label,
                                'type': e.type,
                                'connectivity': e.connectivity,
                                'instanceName': e.instanceName
                            }
                            data[r_name]['elements'].append(element)
                    except OdbError, e:
                        print 'Abaqus error message: %s' % str(e)
                    except:
                        print 'Unknown Exception.'
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

                for frame_id in frames_in_step:
                    print(frame_id)
                    time.append(frames[frame_id].frameValue)

                    # loop of variables
                    for v in variables:
                        v_name = str(v[0])
                        v_position = str(v[1])
                        field_comp = frames[frame_id].fieldOutputs[v_name].getSubset(position=position[v_position], region=region)
                        if len(field_comp.bulkDataBlocks) > 0:
                            bulk_data = field_comp.bulkDataBlocks[0]
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


if __name__ == '__main__':
    setting_file = sys.argv[-1]
    odb_to_npz(setting_file)
