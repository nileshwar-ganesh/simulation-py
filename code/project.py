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
    set_num = 1

    no_split = [3, 9, 15, 17, 18, 11, 16, 2, 4, 19, 6, 12, 7, 5, 14, 10, 8, 13]
    two_split = [20, 29]
    three_split = [21, 28, 1, 22, 24, 26, 27, 25]
    five_split = [23, 30]
    sd_split = [31]

    parameters_no_split = []
    parameters_two_split = []
    parameters_three_split = []
    parameters_five_split = []
    parameters_sd_split = []

    for day in range(1, 32):
        if day in no_split:
            parameters_no_split.append((day, '2019A', 1, 'MA', set_num))

        if day in two_split:
            parameters_two_split.append((day, '2019A', 1, 'MA', set_num, [i/10 for i in range(1, 6)]))
            parameters_two_split.append((day, '2019A', 1, 'MA', set_num, [i/10 for i in range(6, 10)]))

        if day in three_split:
            parameters_three_split.append((day, '2019A', 1, 'MA', set_num, [i/10 for i in range(1, 4)]))
            parameters_three_split.append((day, '2019A', 1, 'MA', set_num, [i/10 for i in range(4, 7)]))
            parameters_three_split.append((day, '2019A', 1, 'MA', set_num, [i/10 for i in range(7, 10)]))

        if day in five_split:
            parameters_five_split.append((day, '2019A', 1, 'MA', set_num, [i/10 for i in range(1, 3)]))
            parameters_five_split.append((day, '2019A', 1, 'MA', set_num, [i/10 for i in range(3, 5)]))
            parameters_five_split.append((day, '2019A', 1, 'MA', set_num, [i/10 for i in range(5, 7)]))
            parameters_five_split.append((day, '2019A', 1, 'MA', set_num, [i/10 for i in range(7, 9)]))
            parameters_five_split.append((day, '2019A', 1, 'MA', set_num, [i/10 for i in range(9, 10)]))

        if day in sd_split:
            slacks = [i/10 for i in range(1, 10)]
            for slack in slacks:
                parameters_sd_split.append((day, '2019A', 1, 'MA', set_num, [slack], [i/10 for i in range(30, 25, -1)]))
                parameters_sd_split.append((day, '2019A', 1, 'MA', set_num, [slack], [i/10 for i in range(25, 19, -1)]))

    parameters = parameters_two_split + parameters_five_split
    scheduler = Scheduler()
    pool = Pool()
    pool.starmap(scheduler.run_specific_day, parameters)

    # scheduler.run_specific_day(2, '2019A', 1, 'MA', set_num)
    print("COMPLETED...")


if __name__ == '__main__':
    operations = Operations()
    operations.clear_all_trace_files()
    operations.clear_all_results()
    operations.clear_all_logs()

    # _run_simulation()
