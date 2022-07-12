import os
import sys
import copy
import math

from schedulingelements import Job, Container, Machine
from functions import Operations
from simulation import Scheduler
from datetime import datetime
from multiprocessing import Pool
from settings import TEST_DATA, RESULT_FOLDER, STATISTICAL_TRACE_FOLDER
from settings import DAYS, SLACKS, SD, MI2011, SETS
from algorithms import AlgorithmGBalanced, AlgorithmGBestFit, AlgorithmThreshold, AlgorithmGMinIdle
from settings import MACHINE_END


def _run_simulation():
    trace_id = '2019A'
    core = 30
    slack_set = 'MA'
    set_num = 1

    no_split = [2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 14, 16, 17, 18, 19]
    two_split = [13, 15, 20]
    three_split = [1, 10, 21, 22, 24, 25, 26, 27, 28, 29]
    five_split = [23]
    nine_split = [30]
    sd_split = [31]

    parameters_no_split = []
    parameters_two_split = []
    parameters_three_split = []
    parameters_five_split = []
    parameters_nine_split = []
    parameters_sd_split = []

    for day in range(1, 32):
        if day in no_split:
            parameters_no_split.append((day, trace_id, core, slack_set, set_num))

        if day in two_split:
            parameters_two_split.append((day, trace_id, core, slack_set, set_num, [i/10 for i in range(1, 6)]))
            parameters_two_split.append((day, trace_id, core, slack_set, set_num, [i/10 for i in range(6, 10)]))

        if day in three_split:
            parameters_three_split.append((day, trace_id, core, slack_set, set_num, [i/10 for i in range(1, 4)]))
            parameters_three_split.append((day, trace_id, core, slack_set, set_num, [i/10 for i in range(4, 7)]))
            parameters_three_split.append((day, trace_id, core, slack_set, set_num, [i/10 for i in range(7, 10)]))

        if day in five_split:
            parameters_five_split.append((day, trace_id, core, slack_set, set_num, [i/10 for i in range(1, 3)]))
            parameters_five_split.append((day, trace_id, core, slack_set, set_num, [i/10 for i in range(3, 5)]))
            parameters_five_split.append((day, trace_id, core, slack_set, set_num, [i/10 for i in range(5, 7)]))
            parameters_five_split.append((day, trace_id, core, slack_set, set_num, [i/10 for i in range(7, 9)]))
            parameters_five_split.append((day, trace_id, core, slack_set, set_num, [i/10 for i in range(9, 10)]))

        if day in nine_split:
            parameters_nine_split.append((day, trace_id, core, slack_set, set_num, [i/10 for i in range(1, 2)]))
            parameters_nine_split.append((day, trace_id, core, slack_set, set_num, [i/10 for i in range(2, 3)]))
            parameters_nine_split.append((day, trace_id, core, slack_set, set_num, [i/10 for i in range(3, 4)]))
            parameters_nine_split.append((day, trace_id, core, slack_set, set_num, [i/10 for i in range(4, 5)]))
            parameters_nine_split.append((day, trace_id, core, slack_set, set_num, [i/10 for i in range(5, 6)]))
            parameters_nine_split.append((day, trace_id, core, slack_set, set_num, [i/10 for i in range(6, 7)]))
            parameters_nine_split.append((day, trace_id, core, slack_set, set_num, [i/10 for i in range(7, 8)]))
            parameters_nine_split.append((day, trace_id, core, slack_set, set_num, [i/10 for i in range(8, 9)]))
            parameters_nine_split.append((day, trace_id, core, slack_set, set_num, [i/10 for i in range(9, 10)]))

        if day in sd_split:
            slacks = [i/10 for i in range(1, 10)]
            for slack in slacks:
                parameters_sd_split.append((day, trace_id, core, slack_set, set_num,
                                            [slack], [i/10 for i in range(30, 26, -1)]))
                parameters_sd_split.append((day, trace_id, core, slack_set, set_num,
                                            [slack], [i/10 for i in range(26, 22, -1)]))
                parameters_sd_split.append((day, trace_id, core, slack_set, set_num,
                                            [slack], [i / 10 for i in range(22, 19, -1)]))

    parameters_batch_1 = parameters_no_split + parameters_three_split
    parameters_batch_2 = parameters_two_split + parameters_five_split + parameters_nine_split + parameters_sd_split

    line = 0
    for param in parameters_batch_1:
        print(param)
        line += 1

    print("Total {} cores.".format(line))

    scheduler = Scheduler()
    pool = Pool()
    pool.starmap(scheduler.run_specific_day, parameters_batch_1)

    # for n, c in enumerate(parameters):
    #    print("File {} with name {}".format(n+1, c))

    # scheduler.run_specific_day(2, '2019A', 1, 'MA', set_num)
    print("COMPLETED...")


def _run_simulation_test():
    scheduler = Scheduler()
    # scheduler.run_specific_day(3, '2019A', 1, 'MA', 1, [0.2], [2.2])
    # scheduler.run_specific_day(3, '2019A', 1, 'MA', 1, [0.3], [2.3])
    # scheduler.run_specific_day_backfill(3, '2019A', 120, 'MA', 5, [0.2], [2.2])
    scheduler.run_specific_day_preemption(2, '2019A', 1, 'MA', 1, [0.9], [2.0])


if __name__ == '__main__':
    operations = Operations()
    operations.clear_all_trace_files()
    operations.clear_all_results()
    operations.clear_all_logs()

    # _run_simulation()
    # _run_simulation_test()
