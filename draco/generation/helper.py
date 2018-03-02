from draco.run import run_draco
from draco.spec import Task
import json

def is_valid(task: Task) -> bool:
    ''' Check a task.
        Args:
            task: a task spec object
        Returns:
            whether the task is valid
    '''
    _, stdout = run_draco(task, files=['define.lp', 'test.lp'], silence_warnings=True)

    return json.loads(stdout)['Result'] != 'UNSATISFIABLE'