import math

from schedulingelements import Job, Container, Machine
from functions import Operations
from settings import TEST_DATA
from settings import DAYS, SLACKS, SD, MI2011, SETS
from algorithms import AlgorithmGBalanced


def _testing_case():
    trace_id = '2011'
    slack_set = 'MA'

    machine_num = 100
    core = 1
    day = 1

    operations = Operations()
    operations.update_system_log('Started simulation.', True)

    #operations.generate_statistical_trace(trace_id, slack_set, core, day)

    file = operations.get_statistical_trace_file_location(trace_id, day, 0.1, 0.033, 1, 1, True)
    jobs = operations.get_jobs(file)
    machines = operations.get_machines(machine_num)
    greedy_balanced = AlgorithmGBalanced(jobs, machines)
    greedy_balanced.execute()


if __name__ == '__main__':
    _testing_case()
