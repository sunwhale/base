# -*- coding: mbcs -*-
try:
    from abaqus import *
    from abaqusConstants import *
    from caeModules import *
    from driverUtils import executeOnCaeStartup
except ImportError:
    print("Without abaqus environment.")


def set_assembly(model_name='Model-1',
                 part_name='PART-1',
                 instance_name='PART-1-1'):

    a = mdb.models[model_name].rootAssembly
    a.DatumCsysByDefault(CARTESIAN)
    p = mdb.models[model_name].parts[part_name]
    a.Instance(name=instance_name, part=p, dependent=ON)


def set_step(model_name='Model-1',
             step_name='Step-1',
             previous='Initial',
             timePeriod=100.0,
             maxNumInc=1000000,
             initialInc=0.1,
             minInc=0.001,
             maxInc=100.0,
             nlgeom=OFF,
             procedure_type='StaticStep'):

    if procedure_type == 'StaticStep':
        mdb.models[model_name].StaticStep(name=step_name, previous=previous,
                                          timePeriod=timePeriod, maxNumInc=maxNumInc, initialInc=initialInc, minInc=minInc,
                                          maxInc=maxInc, nlgeom=nlgeom)

    elif procedure_type == 'CoupledTempDisplacementStep':
        mdb.models[model_name].CoupledTempDisplacementStep(name=step_name,
                                                           previous=previous, response=STEADY_STATE, maxNumInc=maxNumInc,
                                                           initialInc=initialInc, minInc=minInc, maxInc=maxInc, deltmx=None, cetol=None,
                                                           creepIntegration=None, amplitude=RAMP, extrapolation=NONE,
                                                           matrixStorage=UNSYMMETRIC, solutionTechnique=SEPARATED, nlgeom=nlgeom)


def set_output(model_name='Model-1',
               output_name='F-Output-1',
               variables=('LE', 'RF', 'S', 'U'),
               timeInterval=1.0):

    mdb.models[model_name].fieldOutputRequests[output_name].setValues(
        variables=variables, timeInterval=timeInterval)


def set_bc_disp(model_name='Model-1',
                instance_name='PART-1-1',
                set_name='Y0',
                bc_name='BC-1',
                step_name='Step-1',
                u1=UNSET,
                u2=UNSET,
                u3=UNSET,
                ur1=UNSET,
                ur2=UNSET,
                ur3=UNSET,
                amplitude=UNSET):

    a = mdb.models[model_name].rootAssembly
    region = a.instances[instance_name].sets[set_name]
    mdb.models[model_name].DisplacementBC(name=bc_name, createStepName=step_name, region=region,
                                          u1=u1, u2=u2, u3=u3, ur1=ur1, ur2=ur2, ur3=ur3,
                                          amplitude=amplitude, fixed=OFF, distributionType=UNIFORM,
                                          fieldName='', localCsys=None)


def set_bc_symm(model_name='Model-1',
                instance_name='PART-1-1',
                set_name='Y0',
                bc_name='BC-1',
                step_name='Step-1',
                symm_type='XsymmBC'):

    a = mdb.models[model_name].rootAssembly
    region = a.instances[instance_name].sets[set_name]
    if symm_type == 'XsymmBC':
        mdb.models[model_name].XsymmBC(
            name=bc_name, createStepName=step_name, region=region, localCsys=None)
    if symm_type == 'YsymmBC':
        mdb.models[model_name].YsymmBC(
            name=bc_name, createStepName=step_name, region=region, localCsys=None)
    if symm_type == 'ZsymmBC':
        mdb.models[model_name].ZsymmBC(
            name=bc_name, createStepName=step_name, region=region, localCsys=None)


def set_predefined_field(model_name='Model-1',
                         instance_name='PART-1-1',
                         set_name='ALL',
                         field_name='Predefined Field-1',
                         step_name='Initial',
                         magnitudes=(0.0, ),
                         field_type='Temperature'):

    a = mdb.models[model_name].rootAssembly
    region = a.instances[instance_name].sets[set_name]
    if field_type == 'Temperature':
        mdb.models[model_name].Temperature(name=field_name,
                                           createStepName=step_name, region=region, distributionType=UNIFORM,
                                           crossSectionDistribution=CONSTANT_THROUGH_THICKNESS, magnitudes=magnitudes)


def set_job(job_name='Job-1', model_name='Model-1'):
    mdb.Job(name=job_name, model=model_name, description='', type=ANALYSIS,
            atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=90,
            memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True,
            explicitPrecision=SINGLE, nodalOutputPrecision=SINGLE, echoPrint=OFF,
            modelPrint=OFF, contactPrint=OFF, historyPrint=OFF, userSubroutine='',
            scratch='', resultsFormat=ODB, multiprocessingMode=DEFAULT, numCpus=1,
            numGPUs=0)
    mdb.jobs[job_name].writeInput(consistencyChecking=OFF)


if __name__ == "__main__":

    set_assembly(model_name='Model-1',
                 part_name='PART-1',
                 instance_name='PART-1-1')

    set_step(model_name='Model-1',
             step_name='Step-1',
             previous='Initial',
             timePeriod=100.0,
             maxNumInc=1000000,
             initialInc=0.1,
             minInc=0.001,
             maxInc=100.0,
             nlgeom=ON)

    set_output(model_name='Model-1',
               output_name='F-Output-1',
               variables=('LE', 'RF', 'S', 'U'),
               timeInterval=1.0)

    set_bc_disp(model_name='Model-1',
                instance_name='PART-1-1',
                set_name='X0',
                bc_name='BC-1',
                step_name='Step-1',
                u1=0.0,
                amplitude=UNSET)

    set_bc_symm(model_name='Model-1',
                instance_name='PART-1-1',
                set_name='Y0',
                bc_name='BC-1',
                step_name='Step-1',
                symm_type='XsymmBC')

    set_job(job_name='Job-1', model_name='Model-1')
