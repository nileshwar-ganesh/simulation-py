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
from settings import MACHINE_END


def _run_simulation():
    operations = Operations()
    operations.clear_all_trace_files()
    operations.clear_all_results()

    for day in range(1, 2):
        scheduler = Scheduler()
        scheduler.run_specific_day(day, '2019A', 1, 'MA')


if __name__ == '__main__':
    _run_simulation()
