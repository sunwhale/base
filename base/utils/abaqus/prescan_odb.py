# -*- coding: utf-8 -*-
"""

"""
import json

from abaqus import *
from abaqusConstants import *
from odbAccess import *
from textRepr import *


def len_1_level(x):
    if x == None:
        return 0
    else:
        return len(x)


def len_2_level(x):
    if x == None:
        return 0
    else:
        count = 0
        for xx in x:
            count += len(xx)
        return count


def prescan_odb(odb_file):
    with open('.prescan_status', 'w') as f:
        f.write('Scanning')

    odb_dict = {
        'jobData': {},
        'materials': {},
        'name': '',
        'parts': {},
        'path': '',
        'rootAssembly': {},
        'steps': {}
    }

    if os.path.exists(odb_file):
        try:
            odb = openOdb(path=odb_file, readOnly=True)
            odb_dict['name'] = odb.name
            odb_dict['path'] = odb.path

            odb_dict['jobData'] = {
                'precision': str(odb.jobData.precision),
                'version': odb.jobData.version
            }

            odb_dict['rootAssembly'] = {
                'elementSets': {},
                'instances': {},
                'nodeSets': {},
                'surfaces': {}
            }

            for element_set in odb.rootAssembly.elementSets.values():
                odb_dict['rootAssembly']['elementSets'][element_set.name] = {
                    'elements_len': len_2_level(element_set.elements),
                    'instances_len': len(element_set.instances),
                    'name': element_set.name,
                    'nodes_len': len_2_level(element_set.nodes)
                }

            for node_set in odb.rootAssembly.nodeSets.values():
                odb_dict['rootAssembly']['nodeSets'][node_set.name] = {
                    'elements_len': len_2_level(node_set.elements),
                    'instances_len': len(node_set.instances),
                    'name': node_set.name,
                    'nodes_len': len_2_level(node_set.nodes)
                }

            for surface in odb.rootAssembly.surfaces.values():
                odb_dict['rootAssembly']['surfaces'][surface.name] = {
                    'elements_len': len_2_level(surface.elements),
                    'instances_len': len(surface.instances),
                    'name': surface.name,
                    'nodes_len': len_2_level(surface.nodes)
                }

            for instance in odb.rootAssembly.instances.values():
                odb_dict['rootAssembly']['instances'][instance.name] = {
                    'elements_len': len(instance.elements),
                    'instances_len': 1,
                    'name': instance.name,
                    'nodes_len': len(instance.nodes),
                    'elementSets': {},
                    'elements': [],
                    'embeddedSpace': str(instance.embeddedSpace),
                    'nodeSets': {},
                    'nodes': [],
                    'surfaces': {},
                    'type': str(instance.type)
                }

                for element_set in instance.elementSets.values():
                    odb_dict['rootAssembly']['instances'][instance.name]['elementSets'][element_set.name] = {
                        'elements_len': len_1_level(element_set.elements),
                        'instances_len': 1,
                        'name': element_set.name,
                        'nodes_len': len_1_level(element_set.nodes)
                    }

                for node_set in instance.nodeSets.values():
                    odb_dict['rootAssembly']['instances'][instance.name]['nodeSets'][node_set.name] = {
                        'elements_len': len_1_level(node_set.elements),
                        'instances_len': 1,
                        'name': node_set.name,
                        'nodes_len': len_1_level(node_set.nodes)
                    }

                for surface in instance.surfaces.values():
                    odb_dict['rootAssembly']['instances'][instance.name]['surfaces'][surface.name] = {
                        'elements_len': len_1_level(surface.elements),
                        'instances_len': 1,
                        'name': surface.name,
                        'nodes_len': len_1_level(surface.nodes)
                    }

            for step in odb.steps.values():
                odb_dict['steps'][step.name] = {
                    'frames': [],
                    'name': step.name,
                    'nlgeom': step.nlgeom,
                    'number': step.number,
                    'previousStepName': step.previousStepName,
                    'procedure': step.procedure,
                    'timePeriod': step.timePeriod,
                    'totalTime': step.totalTime
                }
                max_len = 16
                frames = step.frames
                frames_len = len(frames)
                if frames_len < max_len:
                    frame_ids = [i for i in range(frames_len)]
                else:
                    frame_ids = [i for i in range(max_len / 2)]
                    frame_ids += [i for i in range(frames_len - int(max_len / 2), frames_len)]

                for i in frame_ids:
                    frame = frames[i]
                    frame_dict = {
                        'description': frame.description,
                        'fieldOutputs': {},
                        'frameId': frame.frameId,
                        'frameValue': frame.frameValue,
                        'incrementNumber': frame.incrementNumber,
                    }

                    for field in frame.fieldOutputs.values():
                        frame_dict['fieldOutputs'][field.name] = {
                            'baseElementTypes': [],
                            'bulkDataBlocks': [],
                            'componentLabels': field.componentLabels,
                            'description': field.description,
                            'locations': [],
                            'name': field.name,
                            'type': str(field.type),
                            'validInvariants': [],
                        }

                        for base_element_type in field.baseElementTypes:
                            frame_dict['fieldOutputs'][field.name]['baseElementTypes'].append(
                                str(base_element_type))

                        for location in field.locations:
                            frame_dict['fieldOutputs'][field.name]['locations'].append(
                                {'position': str(location.position)})

                        for valid_invariant in field.validInvariants:
                            frame_dict['fieldOutputs'][field.name]['validInvariants'].append(
                                str(valid_invariant))
                    odb_dict['steps'][step.name]['frames'].append(frame_dict)
            with open('.prescan_status', 'w') as f:
                f.write('Done')
        except OdbError, e:
            print('OdbError: %s\n' % str(e))
            with open('.prescan_status', 'w') as f:
                f.write('Error')
        except KeyError, e:
            print('KeyError: %s\n' % str(e))
            with open('.prescan_status', 'w') as f:
                f.write('Error')
        except:
            print('Unknown Error\n')
            with open('.prescan_status', 'w') as f:
                f.write('Error')
    else:
        print('The odb file is not found.\n')
        with open('.prescan_status', 'w') as f:
            f.write('Error')

    return odb_dict


if __name__ == '__main__':
    odb_file = sys.argv[-2]
    odb_dict = prescan_odb(odb_file)

    odb_json_file = sys.argv[-1]
    with open(odb_json_file, 'w') as f:
        json.dump(odb_dict, f, ensure_ascii=False)
