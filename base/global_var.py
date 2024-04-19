# -*- coding: utf-8 -*-
"""

"""
from base.utils.events_manager import EventManager, AbaqusSolverListener, AbaqusPostprocListener, EventSource, PyfemSolverListener

abaqus_solver_listener = AbaqusSolverListener('AbaqusSolver')
abaqus_postproc_listener = AbaqusPostprocListener('AbaqusPostproc')
pyfem_solver_listener = PyfemSolverListener('PyfemSolver')
event_manager = EventManager()
event_manager.add_event_listener('AbaqusSolver', abaqus_solver_listener.handler)
event_manager.add_event_listener('odb_to_npz', abaqus_postproc_listener.handler)
event_manager.add_event_listener('PyfemSolver', pyfem_solver_listener.handler)
event_source = EventSource(event_manager)

exporting_threads = {}
sync_threads = {}


def create_thread_id(threads_dict):
    num_of_threads = len(threads_dict.keys())

    if num_of_threads == 0:
        thread_id = 1
    else:
        thread_id = max(num_of_threads, max(list(threads_dict.keys()))) + 1

    return thread_id
