# -*- coding: utf-8 -*-
"""

"""
from abaqus import *
from abaqusConstants import *
from odbAccess import *
from textRepr import *


def print_figure(setting_file, odb_name='Job-1.odb'):
    odb = session.openOdb(name=odb_name)

    session.pngOptions.setValues(imageSize=setting['imageSize'])
    session.printOptions.setValues(vpDecorations=OFF, vpBackground=OFF, reduceColors=False)

    viewport = session.viewports['Viewport: 1']

    viewport.setValues(displayedObject=odb)
    viewport.makeCurrent()
    viewport.setValues(width=200)
    viewport.setValues(height=200)
    viewport.view.setProjection(projection=PARALLEL)
    viewport.viewportAnnotationOptions.setValues(legendBox=ON, title=OFF, state=OFF, annotations=OFF, compass=OFF)
    viewport.viewportAnnotationOptions.setValues(triad=OFF, legend=setting['legend'])

    display = viewport.odbDisplay
    display.commonOptions.setValues(visibleEdges=FREE)
    display.commonOptions.setValues(deformationScaling=UNIFORM, uniformScaleFactor=setting['uniformScaleFactor'])
    display.setFrame(step=setting['step'], frame=setting['frame'])
    display.display.setValues(plotState=setting['plotState'])
    display.contourOptions.setValues(contourStyle=CONTINUOUS)

    if setting['refinement'] != ():
        figurename = '%s_%s' % (setting['refinement'][-1], setting['frame'])
    else:
        figurename = '%s_%s' % (setting['variableLabel'], setting['frame'])

    display.contourOptions.setValues(maxAutoCompute=setting['maxAutoCompute'],
                                     maxValue=setting['maxValue'],
                                     minAutoCompute=setting['minAutoCompute'],
                                     minValue=setting['minValue'])

    display.setPrimaryVariable(variableLabel=setting['variableLabel'],
                               outputPosition=setting['outputPosition'],
                               refinement=setting['refinement'], )

    viewport.view.fitView()
    session.printToFile(fileName=figurename, format=PNG, canvasObjects=(viewport, ))


if __name__ == '__main__':
    setting_file = sys.argv[-1]
    print_figure(setting_file)

    # setting = {
    #     'imageSize': (200, 200),
    #     'legend': OFF,
    #     'plotState': (CONTOURS_ON_UNDEF, ),
    #     'uniformScaleFactor': 1.0,
    #     'step': 'Step-1',
    #     'frame': -1,
    #     'variableLabel': 'NT11',
    #     'outputPosition': NODAL,
    #     'refinement': (),
    #     'maxAutoCompute': OFF,
    #     'maxValue': 1,
    #     'minAutoCompute': OFF,
    #     'minValue': 0
    # }
    # setting = {
    #     'imageSize': (2000, 2000),
    #     'legend': ON,
    #     'plotState': (CONTOURS_ON_DEF, ),
    #     'step': 'Step-1',
    #     'frame': -1,
    #     'variableLabel': 'S',
    #     'outputPosition': INTEGRATION_POINT,
    #     'refinement': (COMPONENT, 'S22'),
    #     'maxAutoCompute': ON,
    #     'maxValue': 1,
    #     'minAutoCompute': ON,
    #     'minValue': 0
    # }
    # setting = {
    #     'imageSize': (2000, 2000),
    #     'legend': ON,
    #     'plotState': (CONTOURS_ON_DEF, ),
    #     'step': 'Step-1',
    #     'frame': -1,
    #     'variableLabel': 'S',
    #     'outputPosition': INTEGRATION_POINT,
    #     'refinement': (INVARIANT, 'Mises'),
    #     'maxAutoCompute': OFF,
    #     'maxValue': 1,
    #     'minAutoCompute': OFF,
    #     'minValue': 0
    # }
