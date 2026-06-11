# -*- coding: utf-8 -*-
"""

"""
import json
import os
import shutil

from abaqus import *
from abaqusConstants import *
from viewerModules import *


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


def unicode_convert(input_data, encode="utf-8"):
    """
    python2中json.loads会默认将字符串解析成unicode，因此需要自行转换为想要的格式
    """
    if isinstance(input_data, dict):
        return {unicode_convert(key, encode): unicode_convert(value) for key, value in input_data.iteritems()}
    elif isinstance(input_data, list):
        return [unicode_convert(element, encode) for element in input_data]
    elif isinstance(input_data, unicode):
        return input_data.encode(encode)
    else:
        return input_data


def print_figure(setting_file, odb_name='Job-1.odb'):
    odb = session.openOdb(name=odb_name)

    setting = load_json(setting_file)
    setting = unicode_convert(setting)

    setting['imageSize'] = eval(setting['imageSize'])
    setting['legend'] = eval(setting['legend'])
    setting['plotState'] = eval(setting['plotState'])
    setting['refinement'] = eval(setting['refinement'])
    setting['outputPosition'] = eval(setting['outputPosition'])
    setting['maxAutoCompute'] = eval(setting['maxAutoCompute'])
    setting['minAutoCompute'] = eval(setting['minAutoCompute'])
    setting['visibleEdges'] = eval(setting['visibleEdges'])
    setting['statusPosition'] = eval(setting['statusPosition'])
    setting['statusRefinement'] = eval(setting['statusRefinement'])
    setting['projection'] = eval(setting['projection'])
    setting['legendPosition'] = eval(setting['legendPosition'])
    setting['mirrorAboutXyPlane'] = eval(setting['mirrorAboutXyPlane'])
    setting['mirrorAboutXzPlane'] = eval(setting['mirrorAboutXzPlane'])
    setting['mirrorAboutYzPlane'] = eval(setting['mirrorAboutYzPlane'])
    setting['triad'] = eval(setting['triad'])
    setting['contourType'] = eval(setting['contourType'])
    setting['contourStyle'] = eval(setting['contourStyle'])
    setting['translucency'] = eval(setting['translucency'])

    session.pngOptions.setValues(imageSize=setting['imageSize'])
    session.printOptions.setValues(vpDecorations=OFF, vpBackground=OFF, reduceColors=False)

    viewport = session.viewports['Viewport: 1']

    viewport.setValues(displayedObject=odb)
    viewport.makeCurrent()
    viewport.setValues(width=setting['width'])
    viewport.setValues(height=setting['height'])
    viewport.view.setValues(session.views[setting['views']])
    viewport.view.setProjection(projection=setting['projection'])
    viewport.viewportAnnotationOptions.setValues(legendBox=ON, title=OFF, state=OFF, annotations=OFF, compass=OFF)
    viewport.viewportAnnotationOptions.setValues(triad=setting['triad'], legend=setting['legend'])
    viewport.viewportAnnotationOptions.setValues(legendPosition=setting['legendPosition'])
    viewport.odbDisplay.basicOptions.setValues(mirrorAboutXyPlane=setting['mirrorAboutXyPlane'], mirrorAboutXzPlane=setting['mirrorAboutXzPlane'], mirrorAboutYzPlane=setting['mirrorAboutYzPlane'])

    region_name = ''
    if setting['removeElementSet'] != '':
        leaf = dgo.LeafFromElementSets(elementSets=(setting['removeElementSet'],))
        viewport.odbDisplay.displayGroup.remove(leaf=leaf)
        region_name = 'remove_' + setting['removeElementSet']

    if setting['replaceElementSet'] != '':
        leaf = dgo.LeafFromElementSets(elementSets=(setting['replaceElementSet'],))
        viewport.odbDisplay.displayGroup.replace(leaf=leaf)
        region_name = 'replace_' + setting['replaceElementSet']

    removeElementSets_str = setting['removeElementSets']
    if removeElementSets_str != '':
        remove_element_set_list = [item.strip() for item in removeElementSets_str.split(',') if item != '']
        leaf = dgo.LeafFromElementSets(elementSets=(remove_element_set_list))
        viewport.odbDisplay.displayGroup.remove(leaf=leaf)
        region_name = 'remove_'

    replaceElementSets_str = setting['replaceElementSets']
    if replaceElementSets_str != '':
        replace_element_set_list = [item.strip() for item in replaceElementSets_str.split(',') if item != '']
        leaf = dgo.LeafFromElementSets(elementSets=(replace_element_set_list))
        viewport.odbDisplay.displayGroup.replace(leaf=leaf)
        region_name = 'replace_'

    region_name += setting['given_name']

    viewport.enableMultipleColors()
    viewport.setColor(initialColor='#BDBDBD')
    cmap = viewport.colorMappings[setting['colorMappings']]
    viewport.setColor(colorMapping=cmap)
    viewport.disableMultipleColors()

    display = viewport.odbDisplay
    display.commonOptions.setValues(visibleEdges=setting['visibleEdges'])
    display.commonOptions.setValues(deformationScaling=UNIFORM, uniformScaleFactor=setting['uniformScaleFactor'])

    if setting['useStatus'] == "True":
        display.setStatusVariable(variableLabel=setting['statusLabel'],
                                  outputPosition=setting['statusPosition'],
                                  refinement=setting['statusRefinement'],
                                  useStatus=True,
                                  statusMinimum=setting['statusMinimum'],
                                  statusMaximum=setting['statusMaximum'])

    display.contourOptions.setValues(maxAutoCompute=setting['maxAutoCompute'],
                                     maxValue=setting['maxValue'],
                                     minAutoCompute=setting['minAutoCompute'],
                                     minValue=setting['minValue'])

    display.setPrimaryVariable(variableLabel=setting['variableLabel'],
                               outputPosition=setting['outputPosition'],
                               refinement=setting['refinement'], )

    display.display.setValues(plotState=setting['plotState'])
    display.contourOptions.setValues(contourType=setting['contourType'], contourStyle=setting['contourStyle'])

    viewport.view.fitView()

    viewport.odbDisplay.commonOptions.setValues(translucency=setting['translucency'], translucencyFactor=setting['translucencyFactor'])
    viewport.view.zoom(zoomFactor=setting['zoomFactor'], mode=ABSOLUTE)
    viewport.view.rotate(xAngle=setting['xAngle'], yAngle=setting['yAngle'], zAngle=setting['zAngle'], mode=MODEL)

    frames_len = len(odb.steps[setting['step']].frames)
    if setting['animate'] == "OFF":
        if setting['frame'] > frames_len - 1:
            setting['frame'] = frames_len - 1
        display.setFrame(step=setting['step'], frame=setting['frame'])

        if setting['refinement'] != ():
            figurename = '%s_%s_%s_%s.png' % (setting['variableLabel'], setting['refinement'][-1], region_name, setting['frame'])
        else:
            figurename = '%s_%s_%s.png' % (setting['variableLabel'], region_name, setting['frame'])
        if setting['plotState'] == (UNDEFORMED,):
            figurename = 'UNDEFORMED_%s_%s_%s.png' % (setting['colorMappings'], region_name, setting['frame'])
        elif setting['plotState'] == (DEFORMED,):
            figurename = 'DEFORMED_%s_%s_%s.png' % (setting['colorMappings'], region_name, setting['frame'])

        session.printToFile(fileName=figurename, format=PNG, canvasObjects=(viewport,))

    elif setting['animate'] == "ON":
        start = setting['startFrame']
        end = setting['endFrame']
        if end > frames_len - 1:
            end = frames_len - 1
        elif end < 0:
            end += frames_len
        interval = setting['frameInterval']

        if setting['refinement'] != ():
            path = '%s_%s_%s' % (setting['variableLabel'], setting['refinement'][-1], region_name)
        else:
            path = '%s_%s' % (setting['variableLabel'], region_name)
        if setting['plotState'] == (UNDEFORMED,):
            path = 'UNDEFORMED_%s_%s' % (setting['colorMappings'], region_name)
        elif setting['plotState'] == (DEFORMED,):
            path = 'DEFORMED_%s_%s' % (setting['colorMappings'], region_name)

        if os.path.exists(path):
            shutil.rmtree(path)
        os.mkdir(path)

        frame_ids = [i for i in range(start, end + 1, interval)]
        if end not in frame_ids:
            frame_ids.append(end)
        for frame_id in frame_ids:
            display.setFrame(step=setting['step'], frame=frame_id)
            if setting['refinement'] != ():
                figurename = '%s%s%s_%s_%s_%s.png' % (path, os.sep, setting['variableLabel'], setting['refinement'][-1], region_name, frame_id)
            else:
                figurename = '%s%s%s_%s_%s.png' % (path, os.sep, setting['variableLabel'], region_name, frame_id)
            if setting['plotState'] == (UNDEFORMED,):
                figurename = '%s%sUNDEFORMED_%s_%s_%s.png' % (path, os.sep, setting['colorMappings'], region_name, frame_id)
            elif setting['plotState'] == (DEFORMED,):
                figurename = '%s%sDEFORMED_%s_%s_%s.png' % (path, os.sep, setting['colorMappings'], region_name, frame_id)

            session.printToFile(fileName=figurename, format=PNG, canvasObjects=(viewport,))

        with open('.print_figure_status', 'w') as f:
            f.write('Done')


if __name__ == '__main__':
    setting_file = sys.argv[-2]
    odb_name = sys.argv[-1]
    print_figure(setting_file, odb_name)
