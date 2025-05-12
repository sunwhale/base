# -*- coding: utf-8 -*-
"""

"""
import os
import json

import numpy as np
from abaqus import *
from abaqusConstants import *
from caeModules import *
from driverUtils import executeOnCaeStartup


def load_json(file_path, encoding='utf-8'):
    """
    Read JSON data from file.
    """
    with open(file_path, 'r') as f:
        return json.load(f)


def is_unicode_all_uppercase(obj):
    return isinstance(obj, unicode) and obj.isupper() and any(c.isalpha() for c in obj)


def interpolate_points(array, n):
    """
    在每两个相邻点之间进行n等分的线性插值

    参数:
        array: 原始二维数组，形状为 (m, 2)
        n: 每两个点之间插入的等分点数(包括第一个点但不包括最后一个点)

    返回:
        插值后的二维数组
    """
    interpolated = []
    for i in range(len(array) - 1):
        # 当前点和下一个点
        p0 = array[i]
        p1 = array[i + 1]

        # 生成从0到1的n+1个等分点(包括0但不包括1)
        t = np.linspace(0, 1, n + 1, endpoint=False)

        # 线性插值
        interpolated_segment = p0 + (p1 - p0) * t[:, np.newaxis]

        # 添加到结果中
        interpolated.append(interpolated_segment)

    # 添加最后一个点
    interpolated.append(np.array([array[-1]]))

    # 合并所有结果
    return np.vstack(interpolated)


def set_material(material_obj, material_dict):
    for material_key, material_value in material_dict.items():
        if hasattr(material_obj, material_key):
            args = {}
            for arg_key, arg_value in material_value.items():
                if is_unicode_all_uppercase(arg_value):
                    args[str(arg_key)] = eval(arg_value)
                else:
                    args[str(arg_key)] = arg_value
            method = getattr(material_obj, material_key)
            method(**args)


def square_wave(width, height, velocity, cycles):
    w = float(width)
    h = float(height)
    v = float(velocity)

    t = (2.0 * w + 4.0 * h) / v

    f0 = np.array([[0, 0, 0],
                   [0, h, h / v],
                   [w, h, h / v + w / v],
                   [w, -h, h / v + w / v + 2 * h / v],
                   [w + w, -h, h / v + w / v + 2 * h / v + w / v],
                   [w + w, 0, h / v + w / v + 2 * h / v + w / v + h / v]])
    f = []
    t_vs_x = []
    t_vs_y = []

    for i in range(int(cycles)):
        for j in range(len(f0)):
            if i == 0:
                f.append([f0[j, 0] + 2 * w * i, f0[j, 1], f0[j, 2] + t * i])
                t_vs_x.append([f0[j, 2] + t * i, f0[j, 0] + 2 * w * i])
                t_vs_y.append([f0[j, 2] + t * i, f0[j, 1]])
            if i > 0 and j > 0:
                f.append([f0[j, 0] + 2 * w * i, f0[j, 1], f0[j, 2] + t * i])
                t_vs_x.append([f0[j, 2] + t * i, f0[j, 0] + 2 * w * i])
                t_vs_y.append([f0[j, 2] + t * i, f0[j, 1]])

    f = np.array(f)

    return f, t_vs_x, t_vs_y


def create_tool(r1, r2, n, depth, pitch, model, part_name):
    theta = 360.0 / n / 180.0 * np.pi

    x0 = -r1 * np.sin(theta)
    y0 = r1 * np.cos(theta)

    if n > 4:
        c1 = (-4.0 * r1 ** 2 * np.sin(theta) ** 2 + r1 ** 2 + r2 ** 2) / (2.0 * r1 * np.cos(theta))
        c2 = np.sin(theta) / np.cos(theta)

        a = 1.0 + c2 ** 2
        b = 2.0 * c1 * c2
        c = c1 ** 2 - r2 ** 2

        x1 = (-b + np.sqrt(b ** 2 - 4.0 * a * c)) / (2.0 * a)
        y1 = np.sqrt(r2 ** 2 - x1 ** 2)
    elif n == 4:
        x1 = (3.0 * r1 ** 2 - r2 ** 2) / (2.0 * r1)
        y1 = np.sqrt(r2 ** 2 - x1 ** 2)

    s = model.ConstrainedSketch(name='Tool', sheetSize=200.0)

    g, v, d, c = s.geometry, s.vertices, s.dimensions, s.constraints
    s.setPrimaryObject(option=STANDALONE)
    s.Line(point1=(0.0, r1), point2=(0.0, r2))
    s.ArcByCenterEnds(center=(0.0, 0.0), point1=(0.0, r2), point2=(x1, y1), direction=CLOCKWISE)
    s.ArcByCenterEnds(center=(x0, y0), point1=(x1, y1), point2=(-x0, y0), direction=CLOCKWISE)
    s.Spot(point=(0.0, 0.0))
    s.radialPattern(geomList=(g[2], g[3], g[4]), vertexList=(), number=n, totalAngle=360.0, centerPoint=(0.0, 0.0))

    p = model.Part(name=part_name, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    p.BaseSolidExtrude(sketch=s, depth=depth, pitch=pitch)
    s.unsetPrimaryObject()
    p.ReferencePoint(point=(0.0, 0.0, 0.0))

    r = p.referencePoints
    refPoints = (r[2],)
    p.Set(cells=p.cells, referencePoints=refPoints, name='SET-TOOL-ALL')
    p.Set(referencePoints=refPoints, name='Set-Tool-RP')
    p.Surface(side1Faces=p.faces, name='Surf-Tool-All')

    return p


def create_plane(x, y, depth, model, part_name):
    s = model.ConstrainedSketch(name='Plane', sheetSize=200.0)

    g, v, d, c = s.geometry, s.vertices, s.dimensions, s.constraints
    s.setPrimaryObject(option=STANDALONE)
    s.rectangle(point1=(0.0, 0.0), point2=(x, y))

    p = mdb.models['Model-1'].Part(name=part_name, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    p.BaseSolidExtrude(sketch=s, depth=depth)
    s.unsetPrimaryObject()

    p.Set(cells=p.cells, name='SET-PLANE-ALL')
    p.Set(faces=p.faces.getByBoundingBox(0, 0, 0, x, y, 0), name='Z0')

    return p


if __name__ == '__main__':
    setting_file = 'setting.json'
    message = load_json(setting_file)

    r1 = message['r1']
    r2 = message['r2']
    n = message['n']
    length = message['length']
    pitch = message['pitch']
    tool_seed_size = message['tool_seed_size']

    x_length_of_plane = message['x_length_of_plane']
    y_length_of_plane = message['y_length_of_plane']
    z_length_of_plane = message['z_length_of_plane']
    plane_seed_size = message['plane_seed_size']

    x_shift_of_tool = message['x_shift_of_tool']
    y_shift_of_tool = message['y_shift_of_tool']
    z_shift_of_tool = message['z_shift_of_tool']

    tool_rotation_speed = message['tool_rotation_speed'] * 2.0 * np.pi / 60.0
    tool_shift_speed = message['tool_shift_speed'] / 60.0

    square_wave_width = message['square_wave_width']
    square_wave_height = message['square_wave_height']
    square_wave_cycles = message['square_wave_cycles']

    output_variables = str(message['output_variables']).replace(' ', '').split(',')
    output_numIntervals = message['output_numIntervals']

    step_time = message['step_time']
    timeIncrementationMethod = message['timeIncrementationMethod']
    userDefinedInc = message['userDefinedInc']

    viewport = session.Viewport(name='Viewport: 1', origin=(0.0, 0.0))
    viewport.makeCurrent()
    viewport.maximize()
    executeOnCaeStartup()
    viewport.partDisplay.geometryOptions.setValues(referenceRepresentation=ON)
    mdb = Mdb()
    viewport.setValues(displayedObject=None)

    model = mdb.models['Model-1']

    set_material(model.Material(name='Material-Tool'), load_json('material_tool.json'))
    set_material(model.Material(name='Material-Plane'), load_json('material_plane.json'))

    model.HomogeneousSolidSection(name='Section-Tool', material='Material-Tool', thickness=None)
    model.HomogeneousSolidSection(name='Section-Plane', material='Material-Plane', thickness=None)

    part_tool = create_tool(r1, r2, n, length, pitch, model, 'Part-1')
    part_plane = create_plane(x_length_of_plane, y_length_of_plane, z_length_of_plane, model, 'Part-2')

    part_tool.SectionAssignment(region=part_tool.sets['SET-TOOL-ALL'], sectionName='Section-Tool', offset=0.0,
                                offsetType=MIDDLE_SURFACE, offsetField='',
                                thicknessAssignment=FROM_SECTION)

    part_plane.SectionAssignment(region=part_plane.sets['SET-PLANE-ALL'], sectionName='Section-Plane', offset=0.0,
                                 offsetType=MIDDLE_SURFACE, offsetField='',
                                 thicknessAssignment=FROM_SECTION)

    c = part_tool.cells
    part_tool.setMeshControls(regions=c, elemShape=TET, technique=FREE)
    elemType1 = mesh.ElemType(elemCode=C3D8RT, elemLibrary=EXPLICIT, secondOrderAccuracy=OFF, distortionControl=DEFAULT)
    elemType2 = mesh.ElemType(elemCode=C3D6T, elemLibrary=EXPLICIT, secondOrderAccuracy=OFF, distortionControl=DEFAULT)
    elemType3 = mesh.ElemType(elemCode=C3D4T, elemLibrary=EXPLICIT, secondOrderAccuracy=OFF, distortionControl=DEFAULT)
    part_tool.setElementType(regions=regionToolset.Region(cells=part_tool.cells), elemTypes=(elemType1, elemType2, elemType3))
    part_tool.seedPart(size=tool_seed_size, deviationFactor=0.1, minSizeFactor=0.1)
    part_tool.generateMesh()

    elemType1 = mesh.ElemType(elemCode=C3D8RT, elemLibrary=EXPLICIT, secondOrderAccuracy=OFF, distortionControl=DEFAULT)
    elemType2 = mesh.ElemType(elemCode=C3D6T, elemLibrary=EXPLICIT, secondOrderAccuracy=OFF, distortionControl=DEFAULT)
    elemType3 = mesh.ElemType(elemCode=C3D4T, elemLibrary=EXPLICIT, secondOrderAccuracy=OFF, distortionControl=DEFAULT)
    part_plane.setElementType(regions=regionToolset.Region(cells=part_tool.cells), elemTypes=(elemType1, elemType2, elemType3))
    part_plane.seedPart(size=plane_seed_size, deviationFactor=0.1, minSizeFactor=0.1)
    part_plane.generateMesh()

    part_plane.Set(nodes=part_plane.nodes, name='NSET-PLANE-ALL')

    a = model.rootAssembly
    a.DatumCsysByDefault(CARTESIAN)
    a.Instance(name='Part-1-1', part=part_tool, dependent=ON)
    a.Instance(name='Part-2-1', part=part_plane, dependent=ON)

    # a.translate(instanceList=('Part-1-1',), vector=(-r2 - tol, y_length_of_plane / 2.0, z_length_of_plane - cut_in))
    a.translate(instanceList=('Part-1-1',), vector=(x_shift_of_tool, y_shift_of_tool, z_shift_of_tool))

    model.RigidBody(name='Constraint-1', refPointRegion=a.instances['Part-1-1'].sets['Set-Tool-RP'],
                    bodyRegion=a.instances['Part-1-1'].sets['SET-TOOL-ALL'])

    set_material(model.ContactProperty('IntProp-1'), load_json('material_interaction.json'))

    model.SurfaceToSurfaceContactExp(name='Int-1',
                                     createStepName='Initial', main=a.instances['Part-1-1'].surfaces['Surf-Tool-All'],
                                     secondary=a.instances['Part-2-1'].sets['NSET-PLANE-ALL'],
                                     mechanicalConstraint=PENALTY, sliding=FINITE,
                                     interactionProperty='IntProp-1', initialClearance=OMIT, datumAxis=None,
                                     clearanceRegion=None)

    if timeIncrementationMethod == 'AUTO':
        model.TempDisplacementDynamicsStep(name='Step-1',
                                           previous='Initial', timePeriod=step_time, scaleFactor=1.0,
                                           massScaling=((SEMI_AUTOMATIC, MODEL, AT_BEGINNING, 1.0, 0.0, None, 0, 0, 0.0, 0.0, 0, None),),
                                           linearBulkViscosity=0.06,
                                           quadBulkViscosity=1.2,
                                           improvedDtMethod=ON)

    elif timeIncrementationMethod == 'FIXED_USER_DEFINED_INC':
        model.TempDisplacementDynamicsStep(name='Step-1',
                                           previous='Initial', timePeriod=step_time,
                                           timeIncrementationMethod=FIXED_USER_DEFINED_INC, userDefinedInc=userDefinedInc,
                                           massScaling=((SEMI_AUTOMATIC, MODEL, AT_BEGINNING, 1.0, 0.0, None, 0, 0, 0.0, 0.0, 0, None),),
                                           linearBulkViscosity=0.06,
                                           quadBulkViscosity=1.2,
                                           improvedDtMethod=ON)

    elif timeIncrementationMethod == 'AUTOMATIC_EBE':
        model.TempDisplacementDynamicsStep(name='Step-1',
                                           previous='Initial', timePeriod=step_time,
                                           timeIncrementationMethod=AUTOMATIC_EBE, scaleFactor=1.0,
                                           massScaling=((SEMI_AUTOMATIC, MODEL, AT_BEGINNING, 1.0, 0.0, None, 0, 0, 0.0, 0.0, 0, None),),
                                           linearBulkViscosity=0.06,
                                           quadBulkViscosity=1.2,
                                           improvedDtMethod=ON)

    else:
        raise KeyError('Unknown timeIncrementationMethod: {}'.format(timeIncrementationMethod))

    f, t_vs_x, t_vs_y = square_wave(width=square_wave_width, height=square_wave_height, velocity=tool_shift_speed, cycles=square_wave_cycles)
    model.TabularAmplitude(name='Amp-x', timeSpan=STEP, smooth=SOLVER_DEFAULT, data=t_vs_x)
    model.TabularAmplitude(name='Amp-y', timeSpan=STEP, smooth=SOLVER_DEFAULT, data=t_vs_y)

    model.DisplacementBC(name='BC-1', createStepName='Initial',
                         region=a.instances['Part-2-1'].sets['Z0'], u1=0.0, u2=0.0, u3=0.0, ur1=0.0, ur2=0.0, ur3=0.0,
                         amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='',
                         localCsys=None)

    model.VelocityBC(name='BC-2', createStepName='Step-1',
                     region=a.instances['Part-1-1'].sets['Set-Tool-RP'], v1=UNSET, v2=UNSET, v3=UNSET, vr1=UNSET, vr2=UNSET,
                     vr3=tool_rotation_speed, amplitude=UNSET, localCsys=None, distributionType=UNIFORM,
                     fieldName='')

    model.DisplacementBC(name='BC-x', createStepName='Step-1',
                         region=a.instances['Part-1-1'].sets['Set-Tool-RP'], u1=1.0, u2=UNSET, u3=UNSET, ur1=UNSET, ur2=UNSET, ur3=UNSET,
                         amplitude='Amp-x', fixed=OFF, distributionType=UNIFORM, fieldName='',
                         localCsys=None)

    model.DisplacementBC(name='BC-y', createStepName='Step-1',
                         region=a.instances['Part-1-1'].sets['Set-Tool-RP'], u1=UNSET, u2=1.0, u3=UNSET, ur1=UNSET, ur2=UNSET, ur3=UNSET,
                         amplitude='Amp-y', fixed=OFF, distributionType=UNIFORM, fieldName='',
                         localCsys=None)

    model.DisplacementBC(name='BC-z', createStepName='Step-1',
                         region=a.instances['Part-1-1'].sets['Set-Tool-RP'], u1=UNSET, u2=UNSET, u3=0.0, ur1=UNSET, ur2=UNSET, ur3=UNSET,
                         amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='',
                         localCsys=None)

    model.DisplacementBC(name='BC-UR', createStepName='Step-1',
                         region=a.instances['Part-1-1'].sets['Set-Tool-RP'], u1=UNSET, u2=UNSET, u3=UNSET, ur1=0.0, ur2=0.0, ur3=UNSET,
                         amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='',
                         localCsys=None)

    model.fieldOutputRequests['F-Output-1'].setValues(numIntervals=output_numIntervals, variables=output_variables)

    mdb.Job(name='Job-1', model='Model-1', description='', type=ANALYSIS,
            atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=90,
            memoryUnits=PERCENTAGE, explicitPrecision=SINGLE,
            nodalOutputPrecision=SINGLE, echoPrint=OFF, modelPrint=OFF,
            contactPrint=OFF, historyPrint=OFF, userSubroutine='', scratch='',
            resultsFormat=ODB, numDomains=1, activateLoadBalancing=False,
            numThreadsPerMpiProcess=1, multiprocessingMode=DEFAULT, numCpus=1)

    mdb.jobs['Job-1'].writeInput(consistencyChecking=OFF)

    a = mdb.models['Model-1'].rootAssembly
    viewport.setValues(displayedObject=a)
    cmap = viewport.colorMappings['Set']
    viewport.setColor(colorMapping=cmap)

    viewport = session.viewports['Viewport: 1']
    viewport.makeCurrent()
    viewport.setValues(width=100)
    viewport.setValues(height=100)

    session.printOptions.setValues(reduceColors=False)
    viewport.view.setValues(session.views['Iso'])
    viewport.view.rotate(xAngle=-90, yAngle=0, zAngle=0, mode=MODEL)
    session.printToFile(fileName='assembly_iso.png', format=PNG, canvasObjects=(viewport,))

    viewport.view.setProjection(projection=PARALLEL)
    viewport.view.setValues(session.views['Bottom'])
    session.printToFile(fileName='assembly_bottom.png', format=PNG, canvasObjects=(viewport,))

    viewport.view.setValues(session.views['Front'])
    session.printToFile(fileName='assembly_front.png', format=PNG, canvasObjects=(viewport,))

    t_vs_x_interpolated = interpolate_points(np.array(t_vs_x), 8)
    t_vs_y_interpolated = interpolate_points(np.array(t_vs_y), 8)
    for i in range(len(t_vs_x_interpolated)):
        a.DatumPointByCoordinate(coords=(t_vs_x_interpolated[i][1] + x_shift_of_tool, t_vs_y_interpolated[i][1] + y_shift_of_tool, z_shift_of_tool))
    viewport.view.setProjection(projection=PARALLEL)
    viewport.view.setValues(session.views['Front'])
    session.printToFile(fileName='assembly_front_with_path.png', format=PNG, canvasObjects=(viewport,))

    # viewport.assemblyDisplay.setValues(mesh=ON)
    # viewport.assemblyDisplay.meshOptions.setValues(meshTechnique=ON)

    viewport = session.viewports['Viewport: 1']
    viewport.partDisplay.setValues(mesh=ON)
    viewport.partDisplay.meshOptions.setValues(meshTechnique=ON)
    viewport.view.setProjection(projection=PERSPECTIVE)
    viewport.partDisplay.geometryOptions.setValues(referenceRepresentation=OFF)

    viewport.setValues(displayedObject=part_tool)
    viewport.view.setValues(session.views['Iso'])
    viewport.view.rotate(xAngle=-90, yAngle=0, zAngle=0, mode=MODEL)
    session.printToFile(fileName='part_tool_mesh_iso.png', format=PNG, canvasObjects=(viewport,))

    viewport.setValues(displayedObject=part_plane)
    viewport.view.setValues(session.views['Iso'])
    viewport.view.rotate(xAngle=-90, yAngle=0, zAngle=0, mode=MODEL)
    session.printToFile(fileName='part_plane_mesh_iso.png', format=PNG, canvasObjects=(viewport,))

    mdb.saveAs(pathName='f1.cae')
