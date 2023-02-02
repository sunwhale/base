# -*- coding: utf-8 -*-
"""

"""

import json
import numpy as np


def read_prescan(odb_json_file):
    with open(odb_json_file, 'r', encoding='utf-8') as f:
        odb_dict = json.load(f)

    variables = {}
    
    for step_key, step in odb_dict['steps'].items():
        fieldOutputs = step['frames'][0]['fieldOutputs']
        for key in fieldOutputs.keys():
            if key not in variables.keys():
                variables[key] = {}
                variables[key]['name'] = key
                variables[key]['description'] = fieldOutputs[key]['description']
                variables[key]['type'] = fieldOutputs[key]['type']
                variables[key]['position'] = fieldOutputs[key]['locations'][0]['position']
                variables[key]['baseElementTypes'] = fieldOutputs[key]['baseElementTypes']
                variables[key]['validInvariants'] = fieldOutputs[key]['validInvariants']
                variables[key]['componentLabels'] = fieldOutputs[key]['componentLabels']
                
                variables[key]['steps'] = []
                variables[key]['steps'].append(step_key)
            else:
                variables[key]['steps'].append(step_key)
                
            # print('Name:', key)
            # print(fieldOutputs[key]['description'])
            # print(fieldOutputs[key]['type'])
            # print(fieldOutputs[key]['locations'][0]['position'])
            # print(fieldOutputs[key]['baseElementTypes'])
            # print(fieldOutputs[key]['validInvariants'])
            # print(fieldOutputs[key]['componentLabels'])
            
    regions = []      
    for nodeset_key, nodeset in odb_dict['rootAssembly']['nodeSets'].items():
        # print(nodeset['name'], nodeset['elements_len'], nodeset['nodes_len'])
        regions.append([nodeset['name'], 'Node set', nodeset['elements_len'], nodeset['nodes_len']])

    for elementset_key, elementset in odb_dict['rootAssembly']['elementSets'].items():
        # print(elementset['name'], elementset['elements_len'], elementset['nodes_len'])
        regions.append([elementset['name'], 'Element set', elementset['elements_len'], elementset['nodes_len']])
  
    for surface_key, surface in odb_dict['rootAssembly']['surfaces'].items():
        # print(surface['name'], surface['elements_len'], surface['nodes_len'])
        regions.append([surface['name'], 'Surface', surface['elements_len'], surface['nodes_len']])

    for instances_key, instances in odb_dict['rootAssembly']['instances'].items():
        # print(instances['name'], instances['elements_len'], instances['nodes_len'])
        regions.append([instances['name'], 'Instance', instances['elements_len'], instances['nodes_len']])
    
        for nset_key, nset in instances['nodeSets'].items():
            # print(instances['name'] + '.' + nset['name'], nset['elements_len'], nset['nodes_len'])
            regions.append([instances['name'] + '.' + nset['name'], 'Node set', nset['elements_len'], nset['nodes_len']])
            
        for elset_key, elset in instances['elementSets'].items():
            # print(instances['name'] + '.' + elset['name'], elset['elements_len'], elset['nodes_len'])
            regions.append([instances['name'] + '.' + elset['name'], 'Element set', elset['elements_len'], elset['nodes_len']])
        
        for surfaceset_key, surfaceset in instances['surfaces'].items():
            # print(instances['name'] + '.' + surfaceset['name'], surfaceset['elements_len'], surfaceset['nodes_len'])
            regions.append([instances['name'] + '.' + surfaceset['name'], 'Surface', surfaceset['elements_len'], surfaceset['nodes_len']])
    
    frames = []
    
    sort_steps = {}
    for step_key, step in odb_dict['steps'].items():
        sort_steps[step['number']] = step
        
    for i in sorted(sort_steps.keys()):
        step = sort_steps[i]
        for frame in step['frames']:
            total_time = step['totalTime'] + frame['frameValue']
            frames.append([step['name'], frame['frameId'], frame['description'], total_time])
        
    return variables, regions, frames


if __name__ == '__main__':

    odb_json_file = 'H:\\files\\abaqus_post\\prescan_odb.json'

    read_prescan(odb_json_file)
