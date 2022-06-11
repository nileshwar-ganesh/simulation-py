import os
import sys
import copy
import math

from schedulingelements import Job, Container, Machine
from functions import Operations
from simulation import Scheduler
from settings import TEST_DATA, RESULT_FOLDER, STATISTICAL_TRACE_FOLDER
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

    jobs = copy.deepcopy(jobs_list)
    machines = copy.deepcopy(machines_list)
    threshold = AlgorithmThreshold(jobs, machines, 0.1)
    threshold.execute()

    jobs = copy.deepcopy(jobs_list)
    machines = copy.deepcopy(machines_list)
    greedy_minidle = AlgorithmGMinIdle(jobs, machines)
    greedy_minidle.execute()


def _run_simulation():
    operations = Operations()
    operations.clear_all_results()
    operations.clear_all_logs()

    scheduler = Scheduler()
    contents = []
    if os.path.exists(STATISTICAL_TRACE_FOLDER):
        contents = os.listdir(STATISTICAL_TRACE_FOLDER)

    for trace_file in contents:
        increment = None
        result_file = "Result" + trace_file[11:]
        machine_start = None
        machine_limit = None
        slack = None
        if "C1" in trace_file:
            increment = 10
            machine_start = 10
            if "D10" in trace_file:
                machine_limit = 191
                slack = 0.5
            elif "D20" in trace_file:
                machine_limit = 141
                slack = 0.1
            elif "D27" in trace_file:
                machine_limit = 111
                slack = 0.9

        if "C30" in trace_file:
            increment = 20
            machine_start = 150
            if "D5" in trace_file:
                machine_limit = 331
            elif "D16" in trace_file:
                machine_limit = 291
            elif "D24" in trace_file:
                machine_limit = 311
            elif "D11" in trace_file:
                machine_limit = 151

        if "C30" in trace_file and "D11" in trace_file:
            scheduler.run_specific_day(trace_file, result_file,
                                       increment, machine_start, machine_limit, slack)

        break

def _test_threshold():
    operations = Operations()
    trace_file = STATISTICAL_TRACE_FOLDER + "GoogleTraceD27L60M0.9SD0.429C1S6.txt"
    machine_num = 50

    jobs = operations.get_jobs(trace_file)
    machines = operations.get_machines(machine_num)

    alg_th = AlgorithmThreshold(jobs, machines, 0.9)
    results_th = alg_th.execute()

    print(results_th)

def _test_threshold_worst_case():
    operations = Operations()
    machine_num = 2

    j1 = Job("J1", 10, 0, 11, 1);
    j2 = Job("J2", 10, 0, 11, 1);
    j3 = Job("J3", 30, 0, 33, 1);

    jobs = [j1, j2 , j3];
    machines = operations.get_machines(machine_num)

    alg_th = AlgorithmThreshold(jobs, machines, 0.1)
    results_th = alg_th.execute()

    print(results_th)





if __name__ == '__main__':
    #_test_threshold()
    #_test_threshold_worst_case()
    _run_simulation()
