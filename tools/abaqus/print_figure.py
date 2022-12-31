# -*- coding: utf-8 -*-
"""

"""
from abaqus import *
from abaqusConstants import *
from viewerModules import *
from driverUtils import executeOnCaeStartup
import json


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

    session.pngOptions.setValues(imageSize=setting['imageSize'])
    session.printOptions.setValues(vpDecorations=OFF, vpBackground=OFF, reduceColors=False)

    viewport = session.viewports['Viewport: 1']

    viewport.setValues(displayedObject=odb)
    viewport.makeCurrent()
    viewport.setValues(width=setting['width'])
    viewport.setValues(height=setting['height'])
    viewport.view.setProjection(projection=PARALLEL)
    viewport.viewportAnnotationOptions.setValues(legendBox=ON, title=OFF, state=OFF, annotations=OFF, compass=OFF)
    viewport.viewportAnnotationOptions.setValues(triad=OFF, legend=setting['legend'])

    viewport.enableMultipleColors()
    viewport.setColor(initialColor='#BDBDBD')
    cmap=viewport.colorMappings[setting['colorMappings']]
    viewport.setColor(colorMapping=cmap)
    viewport.disableMultipleColors()

    display = viewport.odbDisplay
    display.commonOptions.setValues(visibleEdges=setting['visibleEdges'])
    display.commonOptions.setValues(deformationScaling=UNIFORM, uniformScaleFactor=setting['uniformScaleFactor'])
    display.setFrame(step=setting['step'], frame=setting['frame'])
    display.display.setValues(plotState=setting['plotState'])
    display.contourOptions.setValues(contourStyle=CONTINUOUS)

    if setting['useStatus'] == "True":
        display.setStatusVariable(variableLabel=setting['statusLabel'],
                                  outputPosition=setting['statusPosition'],
                                  refinement=setting['statusRefinement'],
                                  useStatus=True,
                                  statusMinimum=setting['statusMinimum'],
                                  statusMaximum=setting['statusMaximum'])

    if setting['refinement'] != ():
        figurename = '%s_%s.png' % (setting['refinement'][-1], setting['frame'])
    else:
        figurename = '%s_%s.png' % (setting['variableLabel'], setting['frame'])

    if setting['plotState'] == (UNDEFORMED, ):
        figurename = 'UNDEFORMED_%s.png' % (setting['colorMappings'])
    elif setting['plotState'] == (DEFORMED, ):
        figurename = 'DEFORMED_%s.png' % (setting['colorMappings'])

    display.contourOptions.setValues(maxAutoCompute=setting['maxAutoCompute'],
                                     maxValue=setting['maxValue'],
                                     minAutoCompute=setting['minAutoCompute'],
                                     minValue=setting['minValue'])

    display.setPrimaryVariable(variableLabel=setting['variableLabel'],
                               outputPosition=setting['outputPosition'],
                               refinement=setting['refinement'], )

    viewport.view.fitView()
    session.printToFile(fileName=figurename, format=PNG,
                        canvasObjects=(viewport, ))


if __name__ == '__main__':
    setting_file = sys.argv[-2]
    odb_name = sys.argv[-1]
    print_figure(setting_file, odb_name)
