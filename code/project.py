import os
import sys
import copy
import math

from schedulingelements import Job, Container, Machine
from functions import Operations
from simulation import Simulation
from settings import TEST_DATA, RESULT_FOLDER
from settings import DAYS, SLACKS, SD, MI2011, SETS
from algorithms import AlgorithmGBalanced, AlgorithmGBestFit, AlgorithmThreshold, AlgorithmGMinIdle


def _testing_case():
    trace_id = '2011'
    slack_set = 'MA'

    machine_num = 4
    core = 1
    day = 1

    operations = Operations()
    operations.clear_all_logs()
    # operations.generate_statistical_trace(trace_id, slack_set, core, day)
    # file = operations.get_statistical_trace_file_location(trace_id, day, 0.1, 0.033, 1, 1, True)
    file = RESULT_FOLDER + 'Jobs4'

    jobs_list = operations.get_jobs(file)
    machines_list = operations.get_machines(machine_num)


    jobs = copy.deepcopy(jobs_list)
    machines = copy.deepcopy(machines_list)
    greedy_balanced = AlgorithmGBalanced(jobs, machines)
    greedy_balanced.execute()

    jobs = copy.deepcopy(jobs_list)
    machines = copy.deepcopy(machines_list)
    greedy_bestfit = AlgorithmGBestFit(jobs.copy(), machines.copy())
    greedy_bestfit.execute()

    """
    jobs = copy.deepcopy(jobs_list)
    machines = copy.deepcopy(machines_list)
    threshold = AlgorithmThreshold(jobs, machines, 0.1)
    threshold.execute()
    """

    jobs = copy.deepcopy(jobs_list)
    machines = copy.deepcopy(machines_list)
    greedy_minidle = AlgorithmGMinIdle(jobs, machines)
    greedy_minidle.execute()

if __name__ == '__main__':
    _testing_case()

