# -*- coding: mbcs -*-
try:
    from abaqus import *
    from abaqusConstants import *
    from caeModules import *
    from driverUtils import executeOnCaeStartup
except ImportError:
    print("Without abaqus environment.")


def set_elastic_material(model_name='Model-1',
                         material_name='MATERIAL-1',
                         table=((65000.0, 0.3), )):

    mdb.models[model_name].Material(name=material_name)
    mdb.models[model_name].materials[material_name].Elastic(
        table=table)


def set_umat_material(model_name='Model-1',
                      material_name='MATERIAL-1',
                      constants=208,
                      depvar=1000,
                      nuvarm=1000,
                      parameters=[]):

    mdb.models[model_name].Material(name=material_name)
    mdb.models[model_name].materials[material_name].Depvar(n=depvar)

    if parameters != []:
        mdb.models[model_name].materials[material_name].UserMaterial(
            mechanicalConstants=parameters[:constants])

    if nuvarm != 0:
        mdb.models[model_name].materials[material_name].UserOutputVariables(
            n=nuvarm)


def set_material_conductivity(model_name='Model-1',
                              material_name='MATERIAL-1',
                              table=((1.0, ), )):

    mdb.models[model_name].materials[material_name].Conductivity(table=table)


def set_solid_section(model_name='Model-1',
                      part_name='PART-1',
                      material_name='MATERIAL-1',
                      section_name='SECTION-1',
                      set_name='ALL',
                      section_thickness=1.0,
                      is_assigment=True):

    p = mdb.models[model_name].parts[part_name]

    mdb.models[model_name].HomogeneousSolidSection(name=section_name,
                                                   material=material_name,
                                                   thickness=section_thickness)


    if is_assigment:
        region = p.sets[set_name]
        p.SectionAssignment(region=region,
                            sectionName=section_name,
                            offset=0.0,
                            offsetType=MIDDLE_SURFACE,
                            offsetField='',
                            thicknessAssignment=FROM_SECTION)


if __name__ == "__main__":

    set_elastic_material(model_name='Model-1',
                         material_name='MATERIAL-1',
                         table=((65000.0, 0.3), ))

    set_umat_material(model_name='Model-1',
                      material_name='MATERIAL-2',
                      constants=208,
                      depvar=1000,
                      nuvarm=1000,
                      parameters=[1,2,3])

    set_solid_section(model_name='Model-1',
                      part_name='PART-1',
                      material_name='MATERIAL-1',
                      section_name='SECTION-1',
                      set_name='ALL',
                      section_thickness=0.01,
                      is_assigment=True)

    set_solid_section(model_name='Model-1',
                      part_name='PART-2',
                      material_name='MATERIAL-2',
                      section_name='SECTION-2',
                      set_name='ALL',
                      section_thickness=None,
                      is_assigment=True)