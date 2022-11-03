# -*- coding: utf-8 -*-
"""

"""

import json
import os
import queue
import time
from Solver import Solver

def monitor():
    while True:
        with open('tasks.msg', 'r', encoding='utf-8') as f:
            task_run_list = json.load(f)
        if len(task_list) == 0:
            break
        
        for task in task_run_list:
            s = Solver(task)
            s.read_msg()
            print(s.cpus, s.solver_status())
            
        time.sleep(5)
        
if __name__ == "__main__":
    task_list = [os.path.join("F:\\Github\\base\\files\\abaqus\\","1","1"), os.path.join("F:\\Github\\base\\files\\abaqus\\","1","2")]
    with open('tasks.msg', 'w', encoding='utf-8') as f:
        json.dump(task_list, f, ensure_ascii=False)
    monitor()
    