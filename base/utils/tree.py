# -*- coding: utf-8 -*-
"""

"""
import json

import numpy as np


def dict_to_tree(obj, start_id, parent_id, tree, depth=0, max_depth=16):
    if depth >= max_depth:
        return start_id

    if isinstance(obj, dict):
        for key, val in obj.items():
            if depth < 1:
                tree.append({"id": start_id,
                             "pId": parent_id,
                             "name": key,
                             "open": True})
            else:
                tree.append({"id": start_id,
                             "pId": parent_id,
                             "name": key})
            start_id += 1
            start_id = dict_to_tree(val, start_id, start_id - 1, tree,
                                    depth=depth + 1, max_depth=max_depth)

    elif isinstance(obj, list):
        max_len = 16
        if len(obj) <= max_len:
            i = 0
            for elem in obj:
                tree.append({"id": start_id,
                             "pId": parent_id,
                             "name": i})
                i += 1
                start_id += 1
                start_id = dict_to_tree(elem, start_id, start_id - 1, tree,
                                        depth=depth, max_depth=max_depth)
        else:
            i = 0
            for elem in obj[:int(max_len / 2)]:
                tree.append({"id": start_id,
                             "pId": parent_id,
                             "name": i})
                i += 1
                start_id += 1
                start_id = dict_to_tree(elem, start_id, start_id - 1, tree,
                                        depth=depth, max_depth=max_depth)

            tree.append({"id": start_id,
                         "pId": parent_id,
                         "name": "..."})
            start_id += 1

            i = 0
            for elem in obj[-int(max_len / 2):]:
                tree.append({"id": start_id,
                             "pId": parent_id,
                             "name": len(obj) - int(max_len / 2) + i})
                i += 1
                start_id += 1
                start_id = dict_to_tree(elem, start_id, start_id - 1, tree,
                                        depth=depth, max_depth=max_depth)

    elif isinstance(obj, str):
        tree.append({"id": start_id,
                     "pId": parent_id,
                     "name": obj})
        start_id += 1

    elif isinstance(obj, np.ndarray):
        if obj.size < 16:
            tree.append({"id": start_id,
                         "pId": parent_id,
                         "name": str(obj)})
        else:
            tree.append({"id": start_id,
                         "pId": parent_id,
                         "name": str(type(obj)) + ".shape" + str(obj.shape)})
        start_id += 1

    else:
        tree.append({"id": start_id,
                     "pId": parent_id,
                     "name": str(obj)})
        start_id += 1

    return start_id


def json_to_ztree(obj):
    tree = []
    dict_to_tree(obj, 1, 0, tree)
    return tree


def odb_json_to_ztree(odb_dict, icon_path):
    tree = []
    icon_path = str(icon_path)

    parent_id = {}
    for i in range(10):
        parent_id[i] = []

    tree.append({"id": len(tree) + 1,
                 "pId": 0, "name": "Datasets",
                 "open": True,
                 "icon": icon_path + 'icoR_adaptiveRemeshRulesSmall.png'})

    parent_id[0].append(len(tree))

    tree.append({"id": len(tree) + 1,
                 "pId": parent_id[0][-1],
                 "name": "File: " + odb_dict['name'],
                 "icon": icon_path + 'icoR_mdbSmall.png'})

    parent_id[1].append(len(tree))

    for step_key, step in odb_dict['steps'].items():
        tree.append({"id": len(tree) + 1,
                     "pId": parent_id[1][-1],
                     "name": step_key,
                     "icon": icon_path + 'icoR_stepSmall.png'})

        parent_id[2].append(len(tree))
        max_len = 8
        if len(step['frames']) <= max_len:
            for frame in step['frames']:
                tree.append({"id": len(tree) + 1,
                             "pId": parent_id[2][-1],
                             "name": frame['description'],
                             "icon": icon_path + 'icoR_framesSmall.png'})

                parent_id[3].append(len(tree))
                for field_name in ['S', 'LE', 'E']:
                    if field_name in frame['fieldOutputs'].keys():
                        tree.append({"id": len(tree) + 1,
                                     "pId": parent_id[3][-1],
                                     "name": field_name})

                        parent_id[4].append(len(tree))

                        tree.append({"id": len(tree) + 1,
                                     "pId": parent_id[4][-1],
                                     "name": "Element types: %s" % str(
                                         frame['fieldOutputs'][field_name]['baseElementTypes'])})

                        tree.append({"id": len(tree) + 1,
                                     "pId": parent_id[4][-1],
                                     "name": "Component labels: %s" % str(
                                         frame['fieldOutputs'][field_name]['componentLabels'])})

                        tree.append({"id": len(tree) + 1,
                                     "pId": parent_id[4][-1],
                                     "name": "Locations: %s" % str(frame['fieldOutputs'][field_name]['locations'])})
        else:
            for frame in step['frames'][:int(max_len / 2)]:
                tree.append({"id": len(tree) + 1,
                             "pId": parent_id[2][-1],
                             "name": frame['description'],
                             "icon": icon_path + 'icoR_framesSmall.png'})

                parent_id[3].append(len(tree))
                for field_name in ['S', 'LE', 'E']:
                    if field_name in frame['fieldOutputs'].keys():
                        tree.append({"id": len(tree) + 1,
                                     "pId": parent_id[3][-1],
                                     "name": field_name})

                        parent_id[4].append(len(tree))

                        tree.append({"id": len(tree) + 1,
                                     "pId": parent_id[4][-1],
                                     "name": "Element types: %s" % str(
                                         frame['fieldOutputs'][field_name]['baseElementTypes'])})

                        tree.append({"id": len(tree) + 1,
                                     "pId": parent_id[4][-1],
                                     "name": "Component labels: %s" % str(
                                         frame['fieldOutputs'][field_name]['componentLabels'])})

                        tree.append({"id": len(tree) + 1,
                                     "pId": parent_id[4][-1],
                                     "name": "Locations: %s" % str(frame['fieldOutputs'][field_name]['locations'])})

            tree.append({"id": len(tree) + 1,
                         "pId": parent_id[2][-1],
                         "name": "..."})

            for frame in step['frames'][-int(max_len / 2):]:
                tree.append({"id": len(tree) + 1,
                             "pId": parent_id[2][-1],
                             "name": frame['description'],
                             "icon": icon_path + 'icoR_framesSmall.png'})

                parent_id[3].append(len(tree))
                for field_name in ['S', 'LE', 'E']:
                    if field_name in frame['fieldOutputs'].keys():
                        tree.append({"id": len(tree) + 1,
                                     "pId": parent_id[3][-1],
                                     "name": field_name})

                        parent_id[4].append(len(tree))

                        tree.append({"id": len(tree) + 1,
                                     "pId": parent_id[4][-1],
                                     "name": "Element types: %s" % str(
                                         frame['fieldOutputs'][field_name]['baseElementTypes'])})

                        tree.append({"id": len(tree) + 1,
                                     "pId": parent_id[4][-1],
                                     "name": "Component labels: %s" % str(
                                         frame['fieldOutputs'][field_name]['componentLabels'])})

                        tree.append({"id": len(tree) + 1,
                                     "pId": parent_id[4][-1],
                                     "name": "Locations: %s" % str(frame['fieldOutputs'][field_name]['locations'])})

    tree.append({"id": len(tree) + 1,
                 "pId": 0, "name": "Groups",
                 "open": True,
                 "icon": icon_path + 'icoR_displayGroupsSmall.png'})

    parent_id[0].append(len(tree))

    for elementset_key, elementset in odb_dict['rootAssembly']['elementSets'].items():
        tree.append({"id": len(tree) + 1,
                     "pId": parent_id[0][-1],
                     "name": elementset['name'],
                     "icon": icon_path + 'icoR_elementSetSmall.png'})
        parent_id[1].append(len(tree))
        tree.append({"id": len(tree) + 1,
                     "pId": parent_id[1][-1],
                     "name": str(elementset['instances_len']) + ' instances'})

        tree.append({"id": len(tree) + 1,
                     "pId": parent_id[1][-1],
                     "name": str(elementset['elements_len']) + ' elements'})

    for instances_key, instances in odb_dict['rootAssembly']['instances'].items():
        for elset_key, elset in instances['elementSets'].items():
            tree.append({"id": len(tree) + 1,
                         "pId": parent_id[0][-1],
                         "name": str(instances['name']) + '.' + str(elset['name']),
                         "icon": icon_path + 'icoR_elementSetSmall.png'})
            parent_id[1].append(len(tree))
            tree.append({"id": len(tree) + 1,
                         "pId": parent_id[1][-1],
                         "name": str(elset['instances_len']) + ' instances'})

            tree.append({"id": len(tree) + 1,
                         "pId": parent_id[1][-1],
                         "name": str(elset['elements_len']) + ' elements'})

    for nodeset_key, nodeset in odb_dict['rootAssembly']['nodeSets'].items():
        tree.append({"id": len(tree) + 1,
                     "pId": parent_id[0][-1],
                     "name": nodeset['name'],
                     "icon": icon_path + 'icoR_nodeSetSmall.png'})
        parent_id[1].append(len(tree))
        tree.append({"id": len(tree) + 1,
                     "pId": parent_id[1][-1],
                     "name": str(nodeset['instances_len']) + ' instances'})

        tree.append({"id": len(tree) + 1,
                     "pId": parent_id[1][-1],
                     "name": str(nodeset['nodes_len']) + ' nodes'})

    for instances_key, instances in odb_dict['rootAssembly']['instances'].items():
        for nset_key, nset in instances['nodeSets'].items():
            tree.append({"id": len(tree) + 1,
                         "pId": parent_id[0][-1],
                         "name": str(instances['name']) + '.' + str(nset['name']),
                         "icon": icon_path + 'icoR_nodeSetSmall.png'})
            parent_id[1].append(len(tree))
            tree.append({"id": len(tree) + 1,
                         "pId": parent_id[1][-1],
                         "name": str(nset['instances_len']) + ' instances'})

            tree.append({"id": len(tree) + 1,
                         "pId": parent_id[1][-1],
                         "name": str(nset['nodes_len']) + ' nodes'})

    for surface_key, surface in odb_dict['rootAssembly']['surfaces'].items():
        tree.append({"id": len(tree) + 1,
                     "pId": parent_id[0][-1],
                     "name": surface['name'], "icon": icon_path + 'icoR_surfaceSetSmall.png'})
        parent_id[1].append(len(tree))
        tree.append({"id": len(tree) + 1,
                     "pId": parent_id[1][-1],
                     "name": str(surface['instances_len']) + ' instances'})
        tree.append({"id": len(tree) + 1,
                     "pId": parent_id[1][-1],
                     "name": str(surface['elements_len']) + ' elements'})
        tree.append({"id": len(tree) + 1,
                     "pId": parent_id[1][-1],
                     "name": str(surface['nodes_len']) + ' nodes'})

    for instances_key, instances in odb_dict['rootAssembly']['instances'].items():
        for surfaceset_key, surfaceset in instances['surfaces'].items():
            tree.append({"id": len(tree) + 1,
                         "pId": parent_id[0][-1],
                         "name": str(instances['name']) + '.' + str(surfaceset['name']),
                         "icon": icon_path + 'icoR_surfaceSetSmall.png'})
            parent_id[1].append(len(tree))
            tree.append({"id": len(tree) + 1,
                         "pId": parent_id[1][-1],
                         "name": str(surfaceset['instances_len']) + ' instances'})
            tree.append({"id": len(tree) + 1,
                         "pId": parent_id[1][-1],
                         "name": str(surfaceset['elements_len']) + ' elements'})
            tree.append({"id": len(tree) + 1,
                         "pId": parent_id[1][-1],
                         "name": str(surfaceset['nodes_len']) + ' nodes'})

    tree.append({"id": len(tree) + 1,
                 "pId": 0,
                 "name": "Assembly",
                 "open": True,
                 "icon": icon_path + 'icoR_connectorSmall.png'})

    tree.append({"id": len(tree) + 1,
                 "pId": len(tree),
                 "name": "Instances",
                 "icon": icon_path + 'icoR_partInstanceSmall.png'})

    parent_id[2].append(len(tree))
    for instance_key, instance in odb_dict['rootAssembly']['instances'].items():
        tree.append({"id": len(tree) + 1,
                     "pId": parent_id[2][-1],
                     "name": instance['name'],
                     "icon": icon_path + 'icoR_partSmall.png'})
        parent_id[3].append(len(tree))
        tree.append({"id": len(tree) + 1,
                     "pId": parent_id[3][-1],
                     "name": str(instance['elements_len']) + ' elements'})

        tree.append({"id": len(tree) + 1,
                     "pId": parent_id[3][-1],
                     "name": str(instance['nodes_len']) + ' nodes'})

    return tree


if __name__ == '__main__':
    # npz = np.load('F:\\Github\\base\\tools\\abaqus\\Job-1.npz',
    #               allow_pickle=True, encoding='latin1')
    # data = npz['data'][()]
    # time = npz['time']

    # ztree = json_to_ztree(data)
    # print(data['PART-1-1.COHESIVESEAM-1-ELEMENTS']['elements'][0])

    odb_json_file = '/files/abaqus/2/1/prescan_odb.json'
    with open(odb_json_file, 'r', encoding='utf-8') as f:
        odb_dict = json.load(f)
    print(list(odb_dict['steps'].keys()))
    print(list(odb_dict['steps']['Step-1']['frames'][0]['fieldOutputs'].keys()))

    fieldOutputs = odb_dict['steps']['Step-1']['frames'][0]['fieldOutputs']

    for key in fieldOutputs.keys():
        print(key)
        print(fieldOutputs[key]['validInvariants'])
        print(fieldOutputs[key]['componentLabels'])
