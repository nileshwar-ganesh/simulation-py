import os
from lido.simulation import Scheduler
from multiprocessing import Pool
from lido.lidosettings import Lido


def _run_simulation():
    # File nomenclature
    # type(preemp/non preemp) - slack set (1, .. ,10) - core (1, 30, 120) - pool (depends on cores)p-s1-c30-1.py
    trace_id = '2019E'
    slack_set = 'MA'
    file_name = os.path.basename(__file__)

    lido = Lido()
    [set_num, core, pool_id] = lido.run_settings(file_name)
    # this is to check whether all results can be obtained within a single run
    parameters_batch = lido.test(trace_id, core, slack_set, set_num, 16)

    scheduler = Scheduler()
    pool = Pool()
    pool.starmap(scheduler.run_specific_day, parameters_batch[pool_id])
    print("COMPLETED...")


if __name__ == '__main__':
    # operations = Operations()
    # operations.clear_all_trace_files()
    # operations.clear_all_results()
    # operations.clear_all_logs()
    _run_simulation()
