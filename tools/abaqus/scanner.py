# -*- coding: utf-8 -*-
"""

"""
from abaqus import *
from abaqusConstants import *
from odbAccess import *


def onOdbPrescan():
    # start to pre-scan the odb file
    odb_file = 'F:\\Github\\base\\tools\\abaqus\\Job-1.odb'
    print('Try to pre-scan the odb file...')

    if os.path.exists(odb_file):
        # try:
        odb = openOdb(path=odb_file, readOnly=True)
        print('Access the odb file successfully.')

        # scan the groups of the assembly
        assembly = odb.rootAssembly
        print('Scan the assembly.')

        regions = []
        variables_items = {}

        for element_set in assembly.elementSets.values():
            elements_in_set = 0
            for elements in element_set.elements:
                elements_in_set += len(elements)
            r = {}
            r['name'] = element_set.name
            r['num_instances'] = len(element_set.instanceNames)
            r['num_elements'] = elements_in_set
            r['num_nodes'] = ''
            r['type'] = 'Element set'
            regions.append(r)

        for node_set in assembly.nodeSets.values():
            nodes_in_set = 0
            for nodes in node_set.nodes:
                nodes_in_set += len(nodes)
            r = {}
            r['name'] = node_set.name
            r['num_instances'] = len(node_set.instanceNames)
            r['num_elements'] = ''
            r['num_nodes'] = nodes_in_set
            r['type'] = 'Node set'
            regions.append(r)

        for surface_set in assembly.surfaces.values():
            nodes_in_set = 0
            for nodes in surface_set.nodes:
                nodes_in_set += len(nodes)
            r = {}
            r['name'] = surface_set.name
            r['num_instances'] = len(surface_set.instanceNames)
            r['num_elements'] = ''
            r['num_nodes'] = nodes_in_set
            r['type'] = 'Surface set'
            regions.append(r)

        instances = assembly.instances.values()
        for instance in instances:
            r = {}
            r['name'] = instance.name
            r['num_instances'] = 1
            r['num_elements'] = len(instance.elements)
            r['num_nodes'] = len(instance.nodes)
            r['type'] = 'Instance'
            regions.append(r)
            for element_set in instance.elementSets.values():
                elements_in_set = len(element_set.elements)
                r = {}
                r['name'] = instance.name + '.' + element_set.name
                r['num_instances'] = 1
                r['num_elements'] = elements_in_set
                r['num_nodes'] = ''
                r['type'] = 'Element set'
                regions.append(r)

        # for r in regions:
            # print(r['name'], r['num_instances'], r['num_elements'], r['num_nodes'], r['type'])
            # print(r)

        # scan the information of the steps
        print('Scan the steps.')
        steps = []
        variables = []
        variables_keys = []

        for step in odb.steps.values():
            # update the table_frames
            # print(step.name, step.totalTime, step.timePeriod)

            # scan the output variables
            variable_in_step = [step.name, {}]
            field_outputs = step.frames[0].fieldOutputs

            for key in field_outputs.keys():
                if key not in variables_keys:
                    variables_keys.append(key)
                    variables_items[key] = {}
                    variables_items[key]['componentLabels'] = field_outputs[key].componentLabels
                    variables_items[key]['validInvariants'] = field_outputs[key].validInvariants
                    variables_items[key]['position'] = field_outputs[key].locations[0].position
                    variables_items[key]['description'] = field_outputs[key].description
                    variables_items[key]['steps'] = []
                    variables_items[key]['steps'].append(step.name)
                else:
                    variables_items[key]['steps'].append(step.name)
                    variable_in_step[1][key] = {}
                    variable_in_step[1][key]['componentLabels'] = field_outputs[key].componentLabels
                    variable_in_step[1][key]['validInvariants'] = field_outputs[key].validInvariants
                    variable_in_step[1][key]['position'] = field_outputs[key].locations[0].position

            variables.append(variable_in_step)

            # scan the frames in a step
            frame_num_in_step = 0
            for frame in step.frames:
                frame_name = 'Increment: ' + str(frame.frameId) + '  (Step time: ' + str(frame.frameValue) + ')'
                print(frame_name)
                field_keys = frame.fieldOutputs.keys()
                for field_key in ['S', 'LE', 'E']:
                    if field_key in field_keys:
                        field = frame.fieldOutputs[field_key]
                        print(field.name)
                        print('Element types: ' + str(field.baseElementTypes))
                        print('Component labels: ' +
                              str(field.componentLabels))
                        print('Locations: ' + str(field.locations[0].position))
                        print('Number of values: ' + str(len(field.values)))

                # update the table_frames
                print(frame_num_in_step)
                frame_num_in_step += 1
                print(str(frame.description))
                print(step.totalTime + frame.frameValue)

        # for variable in variables:
        #     print(variable)

        # update the table_variables
        # step_names = odb.steps.keys()
        # for key in variables_keys:
        #     print(key, variables_items[key]['componentLabels'], variables_items[key]['position'], variables_items[key]['description'])
        #     for v in variables:
        #         if key in v[1].keys():
        #             print(step_names.index(v[0]))

        print('The pre-scan process is finished.')

        # except OdbError, e:
        #     print('Abaqus error message: %s' % str(e))
        # except:
        #     print('Unknown Exception.')

    return 1


if __name__ == '__main__':
    onOdbPrescan()
