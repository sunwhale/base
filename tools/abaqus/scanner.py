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
        try:
            odb = openOdb(path=odb_file, readOnly=True)
            print('Access the odb file successfully.')

            # scan the groups of the assembly
            assembly = odb.rootAssembly
            print('Scan the assembly.')

            regions = []

            for element_set in assembly.elementSets.values():
                print(str(element_set.name))
                
                print(str(len(element_set.instanceNames)) + ' instances')
                elements_in_set = 0
                for elements in element_set.elements:
                    elements_in_set += len(elements)
                print(str(elements_in_set) + ' elements')
                r = {}
                r['name'] = element_set.name
                r['num_instances'] = len(element_set.instanceNames)
                r['num_elements'] = elements_in_set
                r['type'] = 'Element set'
                regions.append(r)
                print(regions)

        #     for node_set in assembly.nodeSets.values():
        #         tree_set = self.tree.addItemLast(tree_groups, node_set.name, self.icon_nodes, self.icon_nodes)
        #         self.tree.addItemLast(tree_set, str(len(node_set.instanceNames)) + ' instances')
        #         nodes_in_set = 0
        #         for nodes in node_set.nodes:
        #             nodes_in_set += len(nodes)
        #         self.tree.addItemLast(tree_set, str(nodes_in_set) + ' nodes')
        #         r = {}
        #         r['name'] = node_set.name
        #         r['num_instances'] = len(node_set.instanceNames)
        #         r['num_nodes'] = nodes_in_set
        #         r['type'] = 'Node set'
        #         self.regions.append(r)

        #     for surface_set in assembly.surfaces.values():
        #         tree_set = self.tree.addItemLast(tree_groups, surface_set.name, self.icon_surfaces, self.icon_surfaces)
        #         self.tree.addItemLast(tree_set, str(len(surface_set.instanceNames)) + ' instances')
        #         nodes_in_set = 0
        #         for nodes in surface_set.nodes:
        #             nodes_in_set += len(nodes)
        #         self.tree.addItemLast(tree_set, str(nodes_in_set) + ' nodes')
        #         r = {}
        #         r['name'] = surface_set.name
        #         r['num_instances'] = len(surface_set.instanceNames)
        #         r['num_nodes'] = nodes_in_set
        #         r['type'] = 'Surface set'
        #         self.regions.append(r)

        #     tree_instance = self.tree.addItemLast(tree_assembly, 'Instances', self.icon_instance, self.icon_instance)
        #     instances = assembly.instances.values()
        #     for instance in instances:
        #         tree_instance_n = self.tree.addItemLast(tree_instance, instance.name, self.icon_parts, self.icon_parts)
        #         self.tree.addItemLast(tree_instance_n, str(len(instance.elements)) + ' elements')
        #         self.tree.addItemLast(tree_instance_n, str(len(instance.nodes)) + ' nodes')
        #         r = {}
        #         r['name'] = instance.name
        #         r['num_elements'] = len(instance.elements)
        #         r['num_nodes'] = len(instance.nodes)
        #         r['type'] = 'Instance'
        #         self.regions.append(r)
        #         for element_set in instance.elementSets.values():
        #             tree_set = self.tree.addItemLast(tree_groups, instance.name + '.' + element_set.name, self.icon_elements, self.icon_elements)
        #             elements_in_set = len(element_set.elements)
        #             self.tree.addItemLast(tree_set, str(elements_in_set) + ' elements')
        #             r = {}
        #             r['name'] = instance.name + '.' + element_set.name
        #             r['num_instances'] = 1
        #             r['num_elements'] = elements_in_set
        #             r['type'] = 'Element set'
        #             self.regions.append(r)

        #     table_regions_row = 1
        #     for r in self.regions:
        #         self.table_regions.insertRows(table_regions_row, 1)
        #         self.table_regions.setItemValue(table_regions_row, 1, r['name'])
        #         self.table_regions.setItemValue(table_regions_row, 2, r['type'])
        #         if r.has_key('num_elements'):
        #             self.table_regions.setItemIntValue(table_regions_row, 3, r['num_elements'])
        #         if r.has_key('num_nodes'):
        #             self.table_regions.setItemIntValue(table_regions_row, 4, r['num_nodes'])
        #         table_regions_row += 1

        #     # scan the information of the steps
        #     scannerDB.setProgress(2)
        #     getAFXApp().getAFXMainWindow().writeToMessageArea('Scan the steps.')

        #     steps = self.odb.steps.values()
        #     table_frames_row = 1
        #     table_frames_num_out = 0
        #     self.variables = []
        #     self.variables_keys = []
        #     table_variables_leading_row_labels = self.table_variables_leading_row_labels

        #     for step in steps:
        #         # update the tree
        #         tree_step = self.tree.addItemLast(tree_file, step.name, self.icon_steps, self.icon_steps)

        #         # update the table_frames
        #         self.table_frames.insertRows(table_frames_row, 1)
        #         self.table_frames.setItemBoolValue(table_frames_row, 0, False)
        #         self.table_frames.disableItem(table_frames_row, 0)
        #         self.table_frames.setItemValue(table_frames_row, 1, step.name)
        #         self.table_frames.setItemFloatValue(table_frames_row, 3, step.totalTime)
        #         self.table_frames.setItemFloatValue(table_frames_row, 4, step.timePeriod)
        #         table_frames_row += 1

        #         # insert the columns of step for the table "table_variables"
        #         numColumns = self.table_variables.getNumColumns()
        #         self.table_variables.insertColumns(numColumns, 1)
        #         self.table_variables.setColumnType(numColumns, self.table_variables.BOOL)
        #         self.table_variables.setColumnJustify(numColumns, AFXTable.CENTER)
        #         table_variables_leading_row_labels += ('\t' + step.name)
        #         self.table_variables.setLeadingRowLabels(table_variables_leading_row_labels)

        #         # scan the output variables
        #         variable_in_step = [step.name, {}]
        #         field_outputs = step.frames[0].fieldOutputs

        #         for key in field_outputs.keys():
        #             if key not in self.variables_keys:
        #                 self.variables_keys.append(key)
        #                 self.variables_items[key] = {}
        #                 self.variables_items[key]['componentLabels'] = field_outputs[key].componentLabels
        #                 self.variables_items[key]['validInvariants'] = field_outputs[key].validInvariants
        #                 self.variables_items[key]['position'] = field_outputs[key].locations[0].position
        #                 self.variables_items[key]['description'] = field_outputs[key].description
        #                 self.variables_items[key]['steps'] = []
        #                 self.variables_items[key]['steps'].append(step.name)
        #             else:
        #                 self.variables_items[key]['steps'].append(step.name)

        #             variable_in_step[1][key] = {}
        #             variable_in_step[1][key]['componentLabels'] = field_outputs[key].componentLabels
        #             variable_in_step[1][key]['validInvariants'] = field_outputs[key].validInvariants
        #             variable_in_step[1][key]['position'] = field_outputs[key].locations[0].position

        #         self.variables.append(variable_in_step)

        #         # scan the frames in a step
        #         scannerDB.setProgress(3)
        #         frame_num_in_step = 0
        #         for frame in step.frames:
        #             # update the tree
        #             tree_frame_name = 'Increment: ' + str(frame.frameId) + '  (Step time: ' + str(frame.frameValue) + ')'
        #             tree_frame = self.tree.addItemLast(tree_step, tree_frame_name, self.icon_increments, self.icon_increments)
        #             field_keys = frame.fieldOutputs.keys()
        #             for field_key in ['S','LE','E']:
        #                 if field_key in field_keys:
        #                     field = frame.fieldOutputs[field_key]
        #                     tree_field = self.tree.addItemLast(tree_frame, field.name)
        #                     self.tree.addItemLast(tree_field, 'Element types: ' + str(field.baseElementTypes))
        #                     self.tree.addItemLast(tree_field, 'Component labels: ' + str(field.componentLabels))
        #                     self.tree.addItemLast(tree_field, 'Locations: ' + str(field.locations[0].position))
        #                     self.tree.addItemLast(tree_field, 'Number of values: ' + str(len(field.values)))

        #             # update the table_frames
        #             self.table_frames.insertRows(table_frames_row, 1)
        #             self.table_frames.setItemBoolValue(table_frames_row, 0, True)
        #             # self.table_frames.setItemIntValue(table_frames_row, 1, table_frames_num_out)
        #             self.table_frames.setItemIntValue(table_frames_row, 1, frame_num_in_step)
        #             frame_num_in_step += 1
        #             table_frames_num_out += 1
        #             self.table_frames.setItemJustify(table_frames_row, 1, AFXTable.RIGHT)
        #             self.table_frames.setItemValue(table_frames_row, 2, str(frame.description))
        #             self.table_frames.setItemFloatValue(table_frames_row, 3, step.totalTime + frame.frameValue)
        #             table_frames_row += 1

        #     # update the total number of frames
        #     self.label_frame.setText(str(table_frames_num_out))

        #     # update the table_variables
        #     scannerDB.setProgress(4)
        #     table_variables_row = 1
        #     step_names = self.odb.steps.keys()
        #     for key in self.variables_keys:
        #         self.table_variables.insertRows(table_variables_row, 1)
        #         self.table_variables.setItemValue(table_variables_row, 1, key)
        #         self.table_variables.setItemValue(table_variables_row, 2, str(self.variables_items[key]['componentLabels']))
        #         self.table_variables.setItemValue(table_variables_row, 3, str(self.variables_items[key]['position']))
        #         self.table_variables.setItemValue(table_variables_row, 4, str(self.variables_items[key]['description']))
                
        #         for v in self.variables:
        #             if key in v[1].keys():
        #                 self.table_variables.setItemBoolValue(table_variables_row, 5 + step_names.index(v[0]), True)

        #         table_variables_row += 1

        #     # expand the sub-root of the tree
        #     self.tree.expandTree(tree_datasets, True)
        #     self.tree.expandTree(tree_groups, True)
        #     self.tree.expandTree(tree_assembly, True)
        #     self.tree.expandTree(tree_material, True)

        #     # self.resize(self.getDefaultWidth(), self.getDefaultHeight())
        #     getAFXApp().getAFXMainWindow().writeToMessageArea('The pre-scan process is finished.')
        #     self.Text_Prompt.setText('The pre-scan process is finished.')

        except OdbError, e:
            print('Abaqus error message: %s' % str(e))
        except:
            print('Unknown Exception.')

    return 1


if __name__ == '__main__':
    onOdbPrescan()
