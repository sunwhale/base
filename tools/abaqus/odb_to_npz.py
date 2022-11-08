# -*- coding: utf-8 -*-
"""
读取odb文件，输出npz格式数据文件
"""
from abaqusConstants import *
from odbAccess import *
import json
import os
import numpy as np

position = {'INTEGRATION_POINT': INTEGRATION_POINT,
            'NODAL': NODAL,
            'ELEMENT_NODAL': ELEMENT_NODAL,
            'CENTROID': CENTROID}


def write_json(file_name, data):
    """
    Write JSON data to file.
    """
    with open(file_name, 'w') as data_file:
        return json.dump(data, data_file)


def read_json(file_name):
    """
    Read JSON data from file.
    """
    with open(file_name, 'r') as data_file:
        return json.loads(data_file.read())


def is_int(s):
    try:
        int(s)
        return True
    except ValueError:
        pass
    return False


def odb_to_npz():
    # Read commands from the file

    cmds = read_json('output_json.txt')
    odbs = cmds['ODB']
    regions = cmds['Regions']
    variables = cmds['Variables']
    step_frames = cmds['Frames']

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

    process_count = 0

    # loop of odbs
    for odb_name in odbs:
        odb = openOdb(path=str(odb_name), readOnly=True)
        data = {}
        time = []
        print(odb_name)
        # loop of regions
        for r in regions:
            # print(r)
            data[str(r[0])] = {}
            data[str(r[0])]['fieldOutputs'] = {}
            data[str(r[0])]['regionType'] = r[1]
            data[str(r[0])]['elements'] = []
            data[str(r[0])]['nodes'] = []

            if r[1] == "Element set":
                if '.' in str(r[0]):
                    instanceName = str(r[0]).split('.')[0]
                    setName = str(r[0]).split('.')[1]
                    try:
                        region = odb.rootAssembly.instances[instanceName].elementSets[setName]
                        for e in region.elements:
                            element = {}
                            element['label'] = e.label
                            element['type'] = e.type
                            element['connectivity'] = e.connectivity
                            element['instanceName'] = e.instanceName
                            data[str(r[0])]['elements'].append(element)
                    except OdbError, e:
                        print 'Abaqus error message: %s' % str(e)
                    except:
                        print 'Unknown Exception.'
                else:
                    region = odb.rootAssembly.elementSets[str(r[0])]
                    for e in region.elements[0]:
                        element = {}
                        element['label'] = e.label
                        element['type'] = e.type
                        element['connectivity'] = e.connectivity
                        element['instanceName'] = e.instanceName
                        data[str(r[0])]['elements'].append(element)

            if r[1] == "Node set":
                region = odb.rootAssembly.nodeSets[str(r[0])]
                for n in region.nodes[0]:
                    node = {}
                    node['label'] = n.label
                    node['coordinates'] = n.coordinates
                    node['instanceName'] = n.instanceName
                    data[str(r[0])]['nodes'].append(node)

            if r[1] == "Instance":
                region = odb.rootAssembly.instances[str(r[0])]
                for e in region.elements:
                    element = {}
                    element['label'] = e.label
                    element['type'] = e.type
                    element['connectivity'] = e.connectivity
                    element['instanceName'] = e.instanceName
                    data[str(r[0])]['elements'].append(element)
                for n in region.nodes:
                    node = {}
                    node['label'] = n.label
                    node['coordinates'] = n.coordinates
                    node['instanceName'] = n.instanceName
                    data[str(r[0])]['nodes'].append(node)

            if r[1] == "Surface set":
                region = odb.rootAssembly.surfaces[str(r[0])]

            for v in variables:
                data[str(r[0])]['fieldOutputs'][str(v[0])] = {}
                data[str(r[0])]['fieldOutputs'][str(v[0])]['position'] = str(v[1])
                data[str(r[0])]['fieldOutputs'][str(v[0])]['baseElementType'] = []
                data[str(r[0])]['fieldOutputs'][str(v[0])]['componentLabels'] = []
                data[str(r[0])]['fieldOutputs'][str(v[0])]['values'] = []
                data[str(r[0])]['fieldOutputs'][str(v[0])]['elementLabels'] = []
                data[str(r[0])]['fieldOutputs'][str(v[0])]['nodeLabels'] = []

            # loop of steps
            time = []
            for step in step_frames:
                frames = odb.steps[str(step[0])].frames

                # loop of frames
                if step[1] == []:
                    step[1] = range(len(frames))

                for frame_id in step[1]:

                    print(frame_id)

                    process_count += 1

                    time.append(frames[frame_id].frameValue)

                    # loop of variables
                    for v in variables:
                        field_comp = frames[frame_id].fieldOutputs[str(v[0])].getSubset(
                            position=position[str(v[1])], region=region)
                        if len(field_comp.bulkDataBlocks) > 0:
                            bulk_data = field_comp.bulkDataBlocks[0]
                            data[str(r[0])]['fieldOutputs'][str(v[0])]['values'].append(np.array(bulk_data.data))
                            if data[str(r[0])]['fieldOutputs'][str(v[0])]['elementLabels'] == []:
                                data[str(r[0])]['fieldOutputs'][str(v[0])]['elementLabels'].append(np.array(bulk_data.elementLabels))
                            if data[str(r[0])]['fieldOutputs'][str(v[0])]['nodeLabels'] == []:
                                data[str(r[0])]['fieldOutputs'][str(v[0])]['nodeLabels'].append(np.array(bulk_data.nodeLabels))
                            if data[str(r[0])]['fieldOutputs'][str(v[0])]['baseElementType'] == []:
                                data[str(r[0])]['fieldOutputs'][str(v[0])]['baseElementType'].append(np.array(bulk_data.baseElementType))
                            if data[str(r[0])]['fieldOutputs'][str(v[0])]['componentLabels'] == []:
                                data[str(r[0])]['fieldOutputs'][str(v[0])]['componentLabels'].append(np.array(bulk_data.componentLabels))

        np.savez(odb_name.replace('.odb', '') + '.npz',
                 data=data,
                 time=time)

        del data
        del time

        odb.close()
