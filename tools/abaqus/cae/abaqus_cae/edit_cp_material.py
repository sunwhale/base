# -*- coding: mbcs -*-
import numpy as np
from abaqus import *
from abaqusConstants import *
from caeModules import *
from driverUtils import executeOnCaeStartup

try:
    from euler_io import read_euler
    from material_io import get_grains_parameters
    print("Use local package.")
except ImportError:
    import sys
    package_path = r'F:\Github\cpfem_czm\func'
    sys.path.append(package_path)
    from euler_io import read_euler
    from material_io import get_grains_parameters
    print("Use package at %s." % package_path)


def edit_cp_materials(model_name='Model-1',
                      part_name='PART-1',
                      grains_parameters=[],
                      grain_prefix='GRAIN_',
                      material_prefix='CP_',
                      constants=208,
                      depvar=1000,
                      nuvarm=1000,
                      section_thickness=0.01):

    grain_id = grains_parameters.keys()

    p = mdb.models[model_name].parts[part_name]

    for i in grain_id:
        print(i)
        parameters = grains_parameters[i]
        grain_name = grain_prefix + str(i)
        material_name = material_prefix + grain_name

        mdb.models[model_name].Material(name=material_name)
        mdb.models[model_name].materials[material_name].Depvar(n=depvar)

        mdb.models[model_name].materials[material_name].UserMaterial(
            mechanicalConstants=parameters[:constants])

        if nuvarm != 0:
            mdb.models[model_name].materials[material_name].UserOutputVariables(
                n=nuvarm)


def edit_cp_sections(model_name='Model-1',
                     part_name='PART-1',
                     grains_parameters=[],
                     grain_prefix='GRAIN_',
                     material_prefix='CP_',
                     section_prefix='',
                     section_thickness=0.01,
                     is_assigment=True):

    grain_id = grains_parameters.keys()

    p = mdb.models[model_name].parts[part_name]

    for i in grain_id:
        print(i)
        parameters = grains_parameters[i]
        grain_name = grain_prefix + str(i)
        material_name = material_prefix + grain_name
        section_name = section_prefix + material_prefix + grain_name

        # create section
        mdb.models[model_name].HomogeneousSolidSection(name=section_name,
                                                       material=material_name,
                                                       thickness=section_thickness)
        # section assignment
        if is_assigment:
            if grain_name in p.sets.keys():
                region = p.sets[grain_name]
                p.SectionAssignment(region=region,
                                    sectionName=section_name,
                                    offset=0.0,
                                    offsetType=MIDDLE_SURFACE,
                                    offsetField='',
                                    thicknessAssignment=FROM_SECTION)


if __name__ == "__main__":

    parameters = np.load(r'parameters.npy')

    grains_euler = read_euler(r'AlSi10Mg_0004.csv')

    grains_parameters = get_grains_parameters(parameters=parameters,
                                              grains_euler=grains_euler)

    edit_cp_materials(model_name='Model-1',
                      part_name='PART-1',
                      grains_parameters=grains_parameters,
                      grain_prefix='GRAIN_',
                      material_prefix='CP_',
                      constants=208,
                      depvar=1000,
                      nuvarm=0,
                      section_thickness=0.01)

    edit_cp_sections(model_name='Model-1',
                     part_name='PART-1',
                     grains_parameters=grains_parameters,
                     grain_prefix='GRAIN_',
                     material_prefix='CP_',
                     section_prefix='',
                     section_thickness=0.01,
                     is_assigment=True)
