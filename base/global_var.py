from utils.events_manager import EventManager, SolverListener, PostprocListener, EventSource

solver_listener = SolverListener('Solver')
postproc_listener = PostprocListener('Postproc')
event_manager = EventManager()
event_manager.add_event_listener('Solver', solver_listener.handler)
event_manager.add_event_listener('odb_to_npz', postproc_listener.handler)
event_source = EventSource(event_manager)

exporting_threads = {}


def create_thread_id():
    num_of_threads = len(exporting_threads.keys())

    if num_of_threads == 0:
        thread_id = 1
    else:
        thread_id = max(num_of_threads, max(list(exporting_threads.keys()))) + 1

    return thread_id
