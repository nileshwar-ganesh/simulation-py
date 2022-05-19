import sys

from functions import Operations
from algorithms import AlgorithmGBalanced, AlgorithmGBestFit, AlgorithmThreshold, AlgorithmGMinIdle
from settings import SETS, SLACKS, SD
from settings import STATISTICAL_TRACE_FOLDER, RESULT_FOLDER
import copy


class Scheduler:

    def __init__(self):
        self.__operations = Operations()

    @staticmethod
    def run_complete(trace_id, slack_set, core, day, machine_num):
        operations = Operations()

        # Generate statistical trace
        operations.generate_statistical_trace(trace_id, slack_set, core, day)

        # Start simulation
        machine_limit = None
        for num in SETS:
            for slack in SLACKS:
                for value in SD:
                    standard_deviation = round(slack/value)
                    # Read jobs
                    job_file = operations.get_statistical_trace_file_location(trace_id, day, slack, standard_deviation,
                                                                              core, num, True)
                    jobs = operations.get_jobs(job_file)

                    if not machine_limit:
                        pass

                    # Initialize machines
                    machines = operations.get_machines(machine_num)

    @staticmethod
    def run_specific_day(trace_file, result_file, increment, machine_start, machine_limit, slack):
        print("Running for file ", trace_file)
        operations = Operations()

        jobs_master = operations.get_jobs(STATISTICAL_TRACE_FOLDER + trace_file)
        print("Total jobs {} on maximum machine setting {}".format(len(jobs_master), machine_limit))

        for m in range(machine_start, machine_limit, increment):
            data = trace_file[11:-4] + ";"
            data += str(m) + ";"
            machines_master = operations.get_machines(m)

            results_gb = None
            results_gbf = None
            results_gmi = None
            results_th = None

            '''
            jobs = copy.deepcopy(jobs_master)
            machines = copy.deepcopy(machines_master)
            greedy_balanced = AlgorithmGBalanced(jobs, machines)
            results_gb = greedy_balanced.execute()
            data += str(results_gb[2]) + ";" + str(results_gb[3]) + ";" + str(results_gb[4]) + ";"

            jobs = copy.deepcopy(jobs_master)
            machines = copy.deepcopy(machines_master)
            greedy_bestfit = AlgorithmGBestFit(jobs.copy(), machines.copy())
            results_gbf = greedy_bestfit.execute()
            data += str(results_gbf[2]) + ";" + str(results_gbf[3]) + ";" + str(results_gbf[4]) + ";"
            '''

            if "C1" in trace_file:
                jobs = copy.deepcopy(jobs_master)
                machines = copy.deepcopy(machines_master)
                threshold = AlgorithmThreshold(jobs, machines, slack)
                results_th = threshold.execute()
                data += str(results_th[2]) + ";" + str(results_th[3]) + ";" + str(results_th[4]) + ";"

            '''
            if "C30" in trace_file:
                jobs = copy.deepcopy(jobs_master)
                machines = copy.deepcopy(machines_master)
                greedy_minidle = AlgorithmGMinIdle(jobs, machines)
                results_gmi = greedy_minidle.execute()
                data += str(results_gmi[2]) + ";" + str(results_gmi[3]) + ";" + str(results_gmi[4]) + ";"
            '''

            print(data)
            data += '\n'
            file = open(RESULT_FOLDER + result_file, "a")
            file.write(data)
            file.close()






