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

    parameters = []
    for day in range(1, 32):
        if day == 1 or day == 2:
            parameters.append((day, '2019A', 1, 'MA', set_num))

    scheduler = Scheduler()
    pool = Pool()
    pool.starmap(scheduler.run_specific_day_limits, parameters)
    print("COMPLETED...")


if __name__ == '__main__':
    operations = Operations()
    operations.clear_all_trace_files()
    operations.clear_all_results()
    operations.clear_all_logs()

    # _run_simulation()
