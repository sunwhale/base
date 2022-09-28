# -*- coding: mbcs -*-
try:
    from abaqus import *
    from abaqusConstants import *
    from caeModules import *
    from driverUtils import executeOnCaeStartup
except ImportError:
    print("Without abaqus environment.")


def create_sketch_base(model_name='Model-1', xsize=[0, 1], ysize=[0, 1]):
    # =============================================================================
    # Sketch-Base
    # =============================================================================
    s = mdb.models[model_name].ConstrainedSketch(name='Sketch-Base',
                                                 sheetSize=200.0)
    g, v, d, c = s.geometry, s.vertices, s.dimensions, s.constraints

    s.rectangle(point1=(xsize[0], ysize[0]),
                point2=(xsize[1], ysize[1]))


def create_part(model_name='Model-1', part_name='PART-1', dimension=2, depth=1.0):
    if dimension == 2:
        # =============================================================================
        # create 2D shell
        # =============================================================================
        p = mdb.models[model_name].Part(name=part_name,
                                        dimensionality=TWO_D_PLANAR,
                                        type=DEFORMABLE_BODY)
        p.BaseShell(sketch=mdb.models[model_name].sketches['Sketch-Base'])
    elif dimension == 3:
        # =============================================================================
        # create 3D extrude solid
        # =============================================================================
        p = mdb.models[model_name].Part(name=part_name,
                                        dimensionality=THREE_D,
                                        type=DEFORMABLE_BODY)
        p.BaseSolidExtrude(
            sketch=mdb.models[model_name].sketches['Sketch-Base'], depth=depth)


def create_all_set(model_name='Model-1', part_name='PART-1', dimension=2):
    # =============================================================================
    # create grains' sets
    # =============================================================================
    p = mdb.models[model_name].parts[part_name]
    if dimension == 2:
        p.Set(name='ALL', faces=p.faces)
    elif dimension == 3:
        p.Set(name='ALL', cells=p.cells)


def create_mesh(model_name='Model-1', part_name='PART-1', dimension=2, elem_code=CPS4):
    p = mdb.models[model_name].parts[part_name]
    p.seedPart(size=1.0, deviationFactor=0.1, minSizeFactor=0.1)
    elemType1 = mesh.ElemType(elemCode=elem_code, elemLibrary=STANDARD,
                              secondOrderAccuracy=OFF, distortionControl=DEFAULT)
    if dimension == 2:
        regions = (p.faces, )
    elif dimension == 3:
        regions = (p.cells, )
    p.setElementType(regions=regions, elemTypes=(elemType1, ))
    p.generateMesh()


if __name__ == "__main__":
    create_sketch_base(model_name='Model-1', xsize=[0, 1], ysize=[0, 1])
    create_part(model_name='Model-1', part_name='PART-1', dimension=2, depth=1.0)
    create_mesh(model_name='Model-1', part_name='PART-1',
                dimension=2, elem_code=CPS4)
    create_all_set(model_name='Model-1', part_name='PART-1', dimension=2)

    create_part(model_name='Model-1', part_name='PART-2', dimension=3, depth=1.0)
    create_mesh(model_name='Model-1', part_name='PART-2',
                dimension=3, elem_code=C3D8)
    create_all_set(model_name='Model-1', part_name='PART-2', dimension=3)