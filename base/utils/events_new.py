# -*- coding: utf-8 -*-
"""

"""
import json
import os


def dump_json(file_name, data):
    """
    Write JSON data to file.
    """
    with open(file_name, 'w') as f:
        return json.dump(data, f)


def load_json(file_name):
    """
    Read JSON data from file.
    """
    with open(file_name, 'r') as f:
        return json.load(f)


def get_events_new(status_file):
    if os.path.exists(status_file):
        current_jobs = load_json(status_file)
    else:
        current_jobs = []

    return current_jobs


def update_events_new(new_jobs, status_file):
    current_jobs = get_events_new(status_file)

    is_modified = False

    for new_job in new_jobs:
        if new_job not in current_jobs:
            is_modified = True
            current_jobs.append(new_job)

    if is_modified:
        dump_json(status_file, current_jobs)


if __name__ == '__main__':
    pass
