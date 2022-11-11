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
                tree.append({"id": start_id, "pId": parent_id,
                             "name": key, "open": True})
            else:
                tree.append({"id": start_id, "pId": parent_id, "name": key})
            start_id += 1
            start_id = dict_to_tree(
                val, start_id, start_id-1, tree, depth=depth+1, max_depth=max_depth)

    elif isinstance(obj, list):
        i = 0
        for elem in obj:
            tree.append({"id": start_id, "pId": parent_id, "name": i})
            i += 1
            start_id += 1
            start_id = dict_to_tree(
                elem, start_id, start_id-1, tree, depth=depth, max_depth=max_depth)

    elif isinstance(obj, str):
        tree.append({"id": start_id, "pId": parent_id, "name": obj})
        start_id += 1
        
    elif isinstance(obj, np.ndarray):
        if obj.size < 16:
            tree.append({"id": start_id, "pId": parent_id, "name": str(obj)})
        else:
            tree.append({"id": start_id, "pId": parent_id, "name": str(type(obj)) + ".shape" + str(obj.shape)})
        start_id += 1

    else:
        tree.append({"id": start_id, "pId": parent_id, "name": str(obj)})
        start_id += 1
        
    return start_id


def json_to_ztree(obj):
    tree = []
    dict_to_tree(obj, 1, 0, tree)
    return tree


if __name__ == '__main__':
    # with open('prescan_odb.json', 'r', encoding='utf-8') as f:
    #     prescan_odb_dict = json.load(f)
        
    # for i in json_to_ztree(prescan_odb_dict):
    #     print(i)
        
    npz = np.load('F:\\Github\\base\\tools\\abaqus\\Job-1.npz', allow_pickle=True, encoding='latin1')
    data = npz['data'][()]
    time = npz['time']
    
    ztree = json_to_ztree(data)
    print(data['PART-1-1.COHESIVESEAM-1-ELEMENTS']['elements'][0])
