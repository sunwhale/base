# -*- coding: mbcs -*-
from set_part import create_sketch_base, create_part, create_mesh, create_all_set
from set_material import set_elastic_material, set_umat_material, set_solid_section
from set_part_boundary import set_part_boundary
from set_others import set_assembly, set_step, set_output, set_bc_symm, set_bc_disp, set_job
try:
    from abaqus import *
    from abaqusConstants import *
    from caeModules import *
    from driverUtils import executeOnCaeStartup
except ImportError:
    print("Without abaqus environment.")


if __name__ == "__main__":

    executeOnCaeStartup()

    Mdb()

    create_sketch_base(model_name='Model-1', xsize=[0, 1], ysize=[0, 1])

    create_part(model_name='Model-1',
                part_name='PART-1',
                dimension=3,
                depth=1.0)

    create_all_set(model_name='Model-1', part_name='PART-1', dimension=3)

    set_part_boundary(model_name='Model-1',
                      part_name='PART-1',
                      dimension=3,
                      tol=1e-6)

    create_mesh(model_name='Model-1',
                part_name='PART-1',
                dimension=3,
                elem_code=C3D8)

    set_umat_material(model_name='Model-1',
                      material_name='MATERIAL-1',
                      constants=8,
                      depvar=256,
                      nuvarm=0,
                      parameters=[1, 2, 3, 4, 5, 6, 7, 0.3])

    set_solid_section(model_name='Model-1',
                      part_name='PART-1',
                      material_name='MATERIAL-1',
                      section_name='SECTION-1',
                      set_name='ALL',
                      section_thickness=None,
                      is_assigment=True)

    set_assembly(model_name='Model-1',
                 part_name='PART-1',
                 instance_name='PART-1-1')

    set_step(model_name='Model-1',
             step_name='Step-1',
             previous='Initial',
             timePeriod=1.0,
             maxNumInc=10000,
             initialInc=1e-2,
             minInc=1e-9,
             maxInc=0.1,
             nlgeom=ON)

    set_output(model_name='Model-1',
               output_name='F-Output-1',
               variables=('LE', 'RF', 'S', 'U'),
               timeInterval=0.01)

    set_bc_disp(model_name='Model-1',
                instance_name='PART-1-1',
                set_name='Y0',
                bc_name='BC-1',
                step_name='Step-1',
                u2=0.0,
                amplitude=UNSET)

    set_bc_disp(model_name='Model-1',
                instance_name='PART-1-1',
                set_name='Y1',
                bc_name='BC-2',
                step_name='Step-1',
                u2=0.1,
                amplitude=UNSET)

    set_bc_symm(model_name='Model-1',
                instance_name='PART-1-1',
                set_name='X0',
                bc_name='BC-3',
                step_name='Step-1',
                symm_type='XsymmBC')

    set_bc_symm(model_name='Model-1',
                instance_name='PART-1-1',
                set_name='Z0',
                bc_name='BC-4',
                step_name='Step-1',
                symm_type='ZsymmBC')

    set_job(job_name='Job-1', model_name='Model-1')

    odb_name = r'Job-1.cae'
    mdb.saveAs(pathName=odb_name)
