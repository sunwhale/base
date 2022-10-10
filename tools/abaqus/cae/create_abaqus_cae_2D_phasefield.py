# -*- coding: mbcs -*-
from abaqus_cae.set_material import (set_elastic_material,
                                     set_material_conductivity,
                                     set_solid_section, set_umat_material)
from abaqus_cae.set_others import (set_assembly, set_bc_disp, set_bc_symm,
                                   set_job, set_output, set_predefined_field,
                                   set_step)
from abaqus_cae.set_part import (create_all_set, create_mesh, create_part,
                                 create_sketch_base)
from abaqus_cae.set_part_boundary import set_part_boundary

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
                dimension=2,
                depth=1.0)

    create_all_set(model_name='Model-1', part_name='PART-1', dimension=2)

    set_part_boundary(model_name='Model-1',
                      part_name='PART-1',
                      dimension=2,
                      tol=1e-6)

    create_mesh(model_name='Model-1',
                part_name='PART-1',
                dimension=2,
                elem_code=CPE4T)

    set_umat_material(model_name='Model-1',
                      material_name='MATERIAL-1',
                      constants=16,
                      depvar=128,
                      nuvarm=0,
                      parameters=[1, 2, 3, 4, 5, 6, 7, 0.3])

    set_material_conductivity(model_name='Model-1',
                              material_name='MATERIAL-1',
                              table=((1.0, ), ))

    set_solid_section(model_name='Model-1',
                      part_name='PART-1',
                      material_name='MATERIAL-1',
                      section_name='SECTION-1',
                      set_name='ALL',
                      section_thickness=1.0,
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
             minInc=1e-2,
             maxInc=1e-2,
             nlgeom=OFF,
             procedure_type='CoupledTempDisplacementStep')

    set_output(model_name='Model-1',
               output_name='F-Output-1',
               variables=('LE', 'RF', 'S', 'U'),
               timeInterval=0.01)

    set_bc_disp(model_name='Model-1',
                instance_name='PART-1-1',
                set_name='Y0',
                bc_name='BC-1',
                step_name='Step-1',
                u1=UNSET,
                u2=0.0,
                ur3=UNSET,
                amplitude=UNSET)

    set_bc_disp(model_name='Model-1',
                instance_name='PART-1-1',
                set_name='X0Y0',
                bc_name='BC-2',
                step_name='Step-1',
                u1=0.0,
                u2=UNSET,
                ur3=UNSET,
                amplitude=UNSET)

    set_bc_disp(model_name='Model-1',
                instance_name='PART-1-1',
                set_name='Y1',
                bc_name='BC-3',
                step_name='Step-1',
                u1=UNSET,
                u2=0.1,
                ur3=UNSET,
                amplitude=UNSET)

    set_predefined_field(model_name='Model-1',
                         instance_name='PART-1-1',
                         set_name='ALL',
                         field_name='Predefined Field-1',
                         step_name='Initial',
                         magnitudes=(0.0, ),
                         field_type='Temperature')

    set_job(job_name='Job-1', model_name='Model-1')

    odb_name = r'Job-1.cae'
    mdb.saveAs(pathName=odb_name)
