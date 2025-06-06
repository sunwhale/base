# -*- coding: utf-8 -*-
"""

"""
import os
import json

import numpy as np
from scipy.interpolate import interp1d

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


def set_obj(obj, attr, attr_dict):
    args = {}
    for arg_key, arg_value in attr_dict.items():
        if is_unicode_all_uppercase(arg_value):
            args[str(arg_key)] = eval(arg_value)
        else:
            args[str(arg_key)] = arg_value
    method = getattr(obj, attr)
    method(**args)


def set_material(material_obj, material_dict):
    for material_key, material_value in material_dict.items():
        print(material_key)
        if '.' in material_key:
            if hasattr(material_obj, material_key.split('.')[1]):
                material_sub_obj = getattr(material_obj, material_key.split('.')[1])
                for material_sub_key, material_sub_value in material_value.items():
                    if hasattr(material_sub_obj, material_sub_key):
                        set_obj(material_sub_obj, material_sub_key, material_sub_value)
        else:
            if hasattr(material_obj, material_key):
                set_obj(material_obj, material_key, material_value)


def square_wave(width, height, depth, velocity, cycles, layers=1, head_shift=0.0, tail_shift=0.0):
    w = float(width)
    h = float(height)
    d = -float(depth)
    v = float(velocity)

    t = (2.0 * w + 4.0 * h) / v

    f0 = np.array([[0, 0, 0],
                   [0, h, h / v],
                   [w, h, h / v + w / v],
                   [w, 0, h / v + w / v + h / v],
                   [w, -h, h / v + w / v + 2 * h / v],
                   [w + w, -h, h / v + w / v + 2 * h / v + w / v],
                   [w + w, 0, h / v + w / v + 2 * h / v + w / v + h / v]])
    f = []

    for l in range(layers):
        t_head_shift = head_shift * t
        t_tail_shift = tail_shift * t
        fl = []

        for c in range(int(cycles)):
            if c == 0:
                x = interp1d(f0[:, 2], f0[:, 0], kind='linear')(t_head_shift)
                y = interp1d(f0[:, 2], f0[:, 1], kind='linear')(t_head_shift)
                f1 = f0[f0[:, 2] > t_head_shift]
                f1 = np.insert(f1, 0, np.array([x, y, head_shift * t]), axis=0)
                for i in range(len(f1)):
                    fl.append([f1[i, 2] + t * c - t_head_shift, f1[i, 0] + 2 * w * c, f1[i, 1], d * l])

            elif c == int(cycles - 1):
                x = interp1d(f0[:, 2], f0[:, 0], kind='linear')(t - t_tail_shift)
                y = interp1d(f0[:, 2], f0[:, 1], kind='linear')(t - t_tail_shift)
                f1 = f0[f0[:, 2] < t - t_tail_shift]
                f1 = np.append(f1, np.array([[x, y, t - t_tail_shift]]), axis=0)
                for i in range(1, len(f1)):
                    fl.append([f1[i, 2] + t * c - t_head_shift, f1[i, 0] + 2 * w * c, f1[i, 1], d * l])

            else:
                for i in range(1, len(f0)):
                    fl.append([f0[i, 2] + t * c - t_head_shift, f0[i, 0] + 2 * w * c, f0[i, 1], d * l])

        if l % 2 == 0:
            fl = np.array(fl)
            fl[:, 0] = fl[:, 0] + (t * cycles - t_head_shift - t_tail_shift) * l + abs(d) / v * l
        else:
            fl = np.array(fl)[::-1]
            fl[:, 0] = fl[::-1, 0]
            fl[:, 0] = fl[:, 0] + (t * cycles - t_head_shift - t_tail_shift) * l + abs(d) / v * l

        f += fl.tolist()

    f = np.array(f)
    f[:, [0, 1, 2]] = f[:, [0, 1, 2]] - f[0, [0, 1, 2]]

    return f


def drill(depth, velocity):
    d = -float(depth)
    v = float(velocity)

    f = [[0, 0, 0, 0], [abs(d) / v, 0, 0, d]]
    f = np.array(f)

    return f


def create_tool(r1, r2, n, depth, pitch, tool_ref_point, model, part_name):
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
    p.ReferencePoint(point=tool_ref_point)

    r = p.referencePoints
    refPoints = (r[2],)
    p.Set(cells=p.cells, name='SET-TOOL-ALL')
    p.Set(referencePoints=refPoints, name='SET-TOOL-RP')
    p.Surface(side1Faces=p.faces, name='SURF-TOOL-ALL')

    b = p.cells.getBoundingBox()
    x0 = b['low'][0]
    y0 = b['low'][1]
    z0 = b['low'][2]
    x1 = b['high'][0]
    y1 = b['high'][1]
    z1 = b['high'][2]
    p.Set(faces=p.faces.getByBoundingBox(x0, y0, z1, x1, y1, z1), name='SET-TOOL-Z1')

    return p


def import_tool(step_file_name, tool_ref_point, model, part_name):
    step = mdb.openStep(step_file_name, scaleFromFile=OFF)
    p = model.PartFromGeometryFile(name=part_name, geometryFile=step, combine=False, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    p.ReferencePoint(point=tool_ref_point)
    r = p.referencePoints
    refPoints = (r[2],)
    p.Set(cells=p.cells, name='SET-TOOL-ALL')
    p.Set(referencePoints=refPoints, name='SET-TOOL-RP')
    p.Surface(side1Faces=p.faces, name='SURF-TOOL-ALL')

    b = p.cells.getBoundingBox()
    x0 = b['low'][0]
    y0 = b['low'][1]
    z0 = b['low'][2]
    x1 = b['high'][0]
    y1 = b['high'][1]
    z1 = b['high'][2]
    p.Set(faces=p.faces.getByBoundingBox(x0, y0, z1, x1, y1, z1), name='SET-TOOL-Z1')

    return p


def create_plane(x, y, depth, model, part_name):
    s = model.ConstrainedSketch(name='Plane', sheetSize=200.0)

    g, v, d, c = s.geometry, s.vertices, s.dimensions, s.constraints
    s.setPrimaryObject(option=STANDALONE)
    s.rectangle(point1=(0.0, 0.0), point2=(x, y))

    p = model.Part(name=part_name, dimensionality=THREE_D, type=DEFORMABLE_BODY)
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

    tool_path_type = message['tool_path_type']
    square_wave_width = message['square_wave_width']
    square_wave_height = message['square_wave_height']
    square_wave_depth = message['square_wave_depth']
    square_wave_head_shift = message['square_wave_head_shift']
    square_wave_tail_shift = message['square_wave_tail_shift']
    square_wave_cycles = message['square_wave_cycles']
    square_wave_layers = message['square_wave_layers']
    drill_depth = message['drill_depth']
    tool_path_file_name = message['tool_path_file_name']

    temperature_tool_z1 = message['temperature_tool_z1']
    temperature_tool_init = message['temperature_tool_init']
    temperature_plane_init = message['temperature_plane_init']

    output_variables = str(message['output_variables']).replace(' ', '').split(',')
    output_numIntervals = message['output_numIntervals']

    step_time = message['step_time']
    timeIncrementationMethod = message['timeIncrementationMethod']
    userDefinedInc = message['userDefinedInc']
    mass_scaling_factor = message['mass_scaling_factor']

    tool_option = message['tool_option']
    step_file_name = str(message['step_file_name'])
    tool_ref_point_x = message['tool_ref_point_x']
    tool_ref_point_y = message['tool_ref_point_y']
    tool_ref_point_z = message['tool_ref_point_z']

    tool_ref_point = (tool_ref_point_x, tool_ref_point_y, tool_ref_point_z)

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

    if tool_option == 'file':
        part_tool = import_tool(step_file_name, tool_ref_point, model, 'Part-1')
    else:
        part_tool = create_tool(r1, r2, n, length, pitch, tool_ref_point, model, 'Part-1')

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

    model.RigidBody(name='Constraint-1', refPointRegion=a.instances['Part-1-1'].sets['SET-TOOL-RP'],
                    bodyRegion=a.instances['Part-1-1'].sets['SET-TOOL-ALL'])

    set_material(model.ContactProperty('IntProp-1'), load_json('material_interaction.json'))

    model.SurfaceToSurfaceContactExp(name='Int-1',
                                     createStepName='Initial', main=a.instances['Part-1-1'].surfaces['SURF-TOOL-ALL'],
                                     secondary=a.instances['Part-2-1'].sets['NSET-PLANE-ALL'],
                                     mechanicalConstraint=PENALTY, sliding=FINITE,
                                     interactionProperty='IntProp-1', initialClearance=OMIT, datumAxis=None,
                                     clearanceRegion=None)

    if timeIncrementationMethod == 'AUTO':
        model.TempDisplacementDynamicsStep(name='Step-1',
                                           previous='Initial', timePeriod=step_time, scaleFactor=1.0,
                                           massScaling=((SEMI_AUTOMATIC, MODEL, AT_BEGINNING, mass_scaling_factor, 0.0, None, 0, 0, 0.0, 0.0, 0, None),),
                                           linearBulkViscosity=0.06,
                                           quadBulkViscosity=1.2,
                                           improvedDtMethod=ON)

    elif timeIncrementationMethod == 'FIXED_USER_DEFINED_INC':
        model.TempDisplacementDynamicsStep(name='Step-1',
                                           previous='Initial', timePeriod=step_time,
                                           timeIncrementationMethod=FIXED_USER_DEFINED_INC, userDefinedInc=userDefinedInc,
                                           massScaling=((SEMI_AUTOMATIC, MODEL, AT_BEGINNING, mass_scaling_factor, 0.0, None, 0, 0, 0.0, 0.0, 0, None),),
                                           linearBulkViscosity=0.06,
                                           quadBulkViscosity=1.2,
                                           improvedDtMethod=ON)

    elif timeIncrementationMethod == 'AUTOMATIC_EBE':
        model.TempDisplacementDynamicsStep(name='Step-1',
                                           previous='Initial', timePeriod=step_time,
                                           timeIncrementationMethod=AUTOMATIC_EBE, scaleFactor=1.0,
                                           massScaling=((SEMI_AUTOMATIC, MODEL, AT_BEGINNING, mass_scaling_factor, 0.0, None, 0, 0, 0.0, 0.0, 0, None),),
                                           linearBulkViscosity=0.06,
                                           quadBulkViscosity=1.2,
                                           improvedDtMethod=ON)

    else:
        raise KeyError('Unknown timeIncrementationMethod: {}'.format(timeIncrementationMethod))

    if tool_path_type == 'square_wave':
        f = square_wave(width=square_wave_width, height=square_wave_height, depth=square_wave_depth, velocity=tool_shift_speed, cycles=square_wave_cycles,
                                                layers=square_wave_layers, head_shift=square_wave_head_shift, tail_shift=square_wave_tail_shift)
    elif tool_path_type == 'drill':
        f = drill(depth=drill_depth, velocity=tool_shift_speed)

    elif tool_path_type == 'tool_path_file':
        f = np.loadtxt(tool_path_file_name, delimiter=',')

    else:
        raise KeyError('Unknown tool_path_type: {}'.format(tool_path_type))

    t_vs_x = f[:, [0, 1]].tolist()
    t_vs_y = f[:, [0, 2]].tolist()
    t_vs_z = f[:, [0, 3]].tolist()

    np.savetxt('tool_path_000.txt', f, delimiter=',')

    model.TabularAmplitude(name='Amp-x', timeSpan=STEP, smooth=SOLVER_DEFAULT, data=t_vs_x)
    model.TabularAmplitude(name='Amp-y', timeSpan=STEP, smooth=SOLVER_DEFAULT, data=t_vs_y)
    model.TabularAmplitude(name='Amp-z', timeSpan=STEP, smooth=SOLVER_DEFAULT, data=t_vs_z)

    model.DisplacementBC(name='BC-PLANE-FIXED', createStepName='Initial',
                         region=a.instances['Part-2-1'].sets['Z0'], u1=0.0, u2=0.0, u3=0.0, ur1=0.0, ur2=0.0, ur3=0.0,
                         amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='',
                         localCsys=None)

    model.VelocityBC(name='BC-TOOL-VR3', createStepName='Step-1',
                     region=a.instances['Part-1-1'].sets['SET-TOOL-RP'], v1=UNSET, v2=UNSET, v3=UNSET, vr1=UNSET, vr2=UNSET,
                     vr3=tool_rotation_speed, amplitude=UNSET, localCsys=None, distributionType=UNIFORM,
                     fieldName='')

    model.DisplacementBC(name='BC-TOOL-U1', createStepName='Step-1',
                         region=a.instances['Part-1-1'].sets['SET-TOOL-RP'], u1=1.0, u2=UNSET, u3=UNSET, ur1=UNSET, ur2=UNSET, ur3=UNSET,
                         amplitude='Amp-x', fixed=OFF, distributionType=UNIFORM, fieldName='',
                         localCsys=None)

    model.DisplacementBC(name='BC-TOOL-U2', createStepName='Step-1',
                         region=a.instances['Part-1-1'].sets['SET-TOOL-RP'], u1=UNSET, u2=1.0, u3=UNSET, ur1=UNSET, ur2=UNSET, ur3=UNSET,
                         amplitude='Amp-y', fixed=OFF, distributionType=UNIFORM, fieldName='',
                         localCsys=None)

    model.DisplacementBC(name='BC-TOOL-U3', createStepName='Step-1',
                         region=a.instances['Part-1-1'].sets['SET-TOOL-RP'], u1=UNSET, u2=UNSET, u3=1.0, ur1=UNSET, ur2=UNSET, ur3=UNSET,
                         amplitude='Amp-z', fixed=OFF, distributionType=UNIFORM, fieldName='',
                         localCsys=None)

    model.DisplacementBC(name='BC-TOOL-UR1', createStepName='Step-1',
                         region=a.instances['Part-1-1'].sets['SET-TOOL-RP'], u1=UNSET, u2=UNSET, u3=UNSET, ur1=0.0, ur2=UNSET, ur3=UNSET,
                         amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='',
                         localCsys=None)

    model.DisplacementBC(name='BC-TOOL-UR2', createStepName='Step-1',
                         region=a.instances['Part-1-1'].sets['SET-TOOL-RP'], u1=UNSET, u2=UNSET, u3=UNSET, ur1=UNSET, ur2=0.0, ur3=UNSET,
                         amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='',
                         localCsys=None)

    model.TemperatureBC(name='BC-TOOL-TEMP', createStepName='Step-1',
                        region=a.instances['Part-1-1'].sets['SET-TOOL-Z1'], fixed=OFF, distributionType=UNIFORM, fieldName='',
                        magnitude=temperature_tool_z1, amplitude=UNSET)

    model.Temperature(name='Predefined Field-1',
                      createStepName='Initial', region=a.instances['Part-1-1'].sets['SET-TOOL-ALL'], distributionType=UNIFORM,
                      crossSectionDistribution=CONSTANT_THROUGH_THICKNESS, magnitudes=(temperature_tool_init,))

    model.Temperature(name='Predefined Field-2',
                      createStepName='Initial', region=a.instances['Part-2-1'].sets['SET-PLANE-ALL'], distributionType=UNIFORM,
                      crossSectionDistribution=CONSTANT_THROUGH_THICKNESS, magnitudes=(temperature_plane_init,))

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
    cmap = viewport.colorMappings['Section']
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

    t_vs_x_interpolated = interpolate_points(np.array(t_vs_x), 2)
    t_vs_y_interpolated = interpolate_points(np.array(t_vs_y), 2)
    t_vs_z_interpolated = interpolate_points(np.array(t_vs_z), 2)
    for i in range(len(t_vs_x_interpolated)):
        a.DatumPointByCoordinate(coords=(t_vs_x_interpolated[i][1] + x_shift_of_tool, t_vs_y_interpolated[i][1] + y_shift_of_tool, t_vs_z_interpolated[i][1]))
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
