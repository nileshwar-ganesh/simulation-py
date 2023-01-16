import os
import copy

from code.functions import Operations
from lido.simulation import Scheduler
from multiprocessing import Pool
from code.algorithms import AlgorithmOSScheduling, AlgorithmRegion
from lido.lidosettings import Lido


def _run_single_day():
    # File nomenclature
    # type(preemp/non preemp) - slack set (1, .. ,10) - core (1, 30, 120) - pool (depends on cores)p-s1-c30-1.py
    trace_id = '2019A'
    slack_set = 'MA'
    file_name = os.path.basename(__file__)
    set_num = 1
    core = 1
    slack = 0.8

    trace_file = '/home/nileshwar-gk/Projects/simulation-py/statisticaltraces/runningtrace/' \
                 'GoogleTrace2019AD2L60M0.1SD0.033C1S1.txt'
    operation = Operations()
    jobs_master = operation.get_jobs(trace_file)
    machine_master = operation.get_machines(1)
    jobs = copy.deepcopy(jobs_master)
    machines = copy.deepcopy(machine_master)
    alg_oss = AlgorithmOSScheduling(jobs, machines, slack)
    res_oss = alg_oss.execute()

    jobs = copy.deepcopy(jobs_master)
    machines = copy.deepcopy(machine_master)
    alg_reg = AlgorithmRegion(jobs, machines, slack)
    res_reg = alg_reg.execute()

    text_oss = "OSS : {}, {}, {} - ".format(res_oss[2], res_oss[3], res_oss[4])
    text_reg = "REG : {}, {}, {}".format(res_reg[2], res_reg[3], res_reg[4])

    print(text_oss + text_reg)


def _run_simulation():
    # File nomenclature
    # type(preemp/non preemp) - slack set (1, .. ,10) - core (1, 30, 120) - pool (depends on cores)p-s1-c30-1.py
    trace_id = '2019A'
    slack_set = 'MA'
    file_name = os.path.basename(__file__)
    # print(file_name.strip().split('-'))

    lido = Lido()
    [set_num, core, pool_id] = lido.run_settings(file_name)
    parameters_batch = lido.test(trace_id, core, slack_set, set_num, 18)

    # print("Starting for pool {}, with total occupied cores {}".format(pool_id, len(parameters_batch[pool_id])))

    scheduler = Scheduler()
    pool = Pool()
    pool.starmap(scheduler.run_specific_day_preemption, parameters_batch[pool_id])
    print("COMPLETED...")


if __name__ == '__main__':
    operations = Operations()
    operations.clear_all_trace_files()
    operations.clear_all_results()
    operations.clear_all_logs()
    _run_simulation()
