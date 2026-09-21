"""Abaqus/CAE adapter. Requires an Abaqus release with Python 3 support."""
import os
from calibration import relative_displacement


def run_and_measure(input_file, job_name, step_name, first, second, cpus):
    from abaqus import mdb
    from abaqusConstants import COMPLETED, ON
    from odbAccess import openOdb

    previous_directory = os.getcwd()
    try:
        os.chdir(str(input_file.parent))
        if job_name in mdb.jobs:
            raise ValueError('Job name already exists in this CAE session')
        job = mdb.JobFromInputFile(name=job_name,
                                  inputFileName=str(input_file), numCpus=cpus)
        job.submit(consistencyChecking=ON)
        job.waitForCompletion()
        if job.status != COMPLETED:
            raise RuntimeError('Abaqus job did not complete: %s' % job.status)
        odb = openOdb(path=str(input_file.parent / (job_name + '.odb')), readOnly=True)
        try:
            step = odb.steps[step_name]
            if len(step.frames) < 2:
                raise RuntimeError('No completed response frame available')
            frame = step.frames[-1]
            if abs(frame.frameValue - step.timePeriod) > max(1e-8, abs(step.timePeriod) * 1e-6):
                raise RuntimeError('Final frame does not reach the requested step end')
            field = frame.fieldOutputs['U']
            def records():
                for value in field.values:
                    components = value.dataDouble if str(value.precision) == 'DOUBLE_PRECISION' else value.data
                    yield value.instance.name, value.nodeLabel, components
            return relative_displacement(records(), first, second)
        finally:
            odb.close()
    finally:
        os.chdir(previous_directory)
