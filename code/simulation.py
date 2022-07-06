import sys

from functions import Operations
from algorithms import AlgorithmGBalanced, AlgorithmGBestFit, AlgorithmThreshold, AlgorithmGMinIdle
from settings import SETS, SLACKS, SD
from settings import STATISTICAL_TRACE_FOLDER, RESULT_FOLDER
from settings import MACHINE_START
from datetime import datetime
import math
import copy
import time


class Scheduler:

    def __init__(self):
        self.__operations = Operations()

    def run_specific_day(self, day, trace_id, core, slack_set, num, slacks=SLACKS, sd=SD):
        self.__operations.update_parallel_log(day, core, 'start')

        trace_jobs = self.__operations.read_jobs_iso(trace_id, day, core)

        # for num in SETS:
        if True:
            result_file = RESULT_FOLDER + self.__operations.get_result_file_name(trace_id, day, core, num, slacks, sd)
            with open(result_file, "w") as file:
                header = "SET; SLACK; SD; MACHINES; DENOMINATOR; "
                header += "ACC JOBS GB; REJ JOBS GB; ACC LOAD GB; REJ LOAD GB; TOT LOAD GB; RUN TIME GB; "
                header += "ACC JOBS GBF; REJ JOBS GBF; ACC LOAD GBF; REJ LOAD GBF; TOT LOAD GBF; RUN TIME GBF; "
                if core == 1:
                    header += "ACC JOBS TH; REJ JOBS TH; ACC LOAD TH; REJ LOAD TH; TOT LOAD TH; RUN TIME TH; "
                else:
                    header += "ACC JOBS GMI; REJ JOBS GMI; ACC LOAD GMI; REJ LOAD GMI; TOT LOAD GMI; RUN TIME GMI; "
                header += "OPT LOAD; "
                header += "\n"
                file.write(header)
            file.close()

            for slack in slacks:
                for value in sd:

                    standard_deviation = round(slack/value, 3)

                    job_file = self.__operations.get_statistical_trace_file_location(trace_id, day, slack,
                                                                                     standard_deviation, core, num,
                                                                                     True)

                    if job_file is None:
                        self.__operations.generate_statistical_trace_iso(trace_jobs, trace_id, day, core,
                                                                         slack_set, slack, standard_deviation, num)
                        job_file = self.__operations.get_statistical_trace_file_location(trace_id, day, slack,
                                                                                         standard_deviation, core, num,
                                                                                         True)
                    else:
                        print("Waiting for 60s before staring next operation...")
                        time.sleep(60)
                        print("Wait completed...")

                    jobs_master = self.__operations.get_jobs(job_file)

                    [machine_start, machine_end, machine_increment] = self.__operations.get_machine_settings(trace_id,
                                                                                                             day,
                                                                                                             core)

                    for machine_num in range(machine_start, machine_end+1, machine_increment):
                        data = ""
                        data += "{}; {}; {}; {}; {}; ".format(num, slack, standard_deviation, machine_num, value)

                        machines_master = self.__operations.get_machines(machine_num)

                        jobs = copy.deepcopy(jobs_master)
                        machines = copy.deepcopy(machines_master)
                        greedy_balanced = AlgorithmGBalanced(jobs, machines)
                        results_gb = greedy_balanced.execute()
                        data += "{}; {}; {}; {}; {}; {}; ".format(results_gb[0], results_gb[1], results_gb[2],
                                                                  results_gb[3], results_gb[4], results_gb[5])

                        jobs = copy.deepcopy(jobs_master)
                        machines = copy.deepcopy(machines_master)
                        greedy_bestfit = AlgorithmGBestFit(jobs, machines)
                        results_gbf = greedy_bestfit.execute()
                        data += "{}; {}; {}; {}; {}; {}; ".format(results_gbf[0], results_gbf[1], results_gbf[2],
                                                                  results_gbf[3], results_gbf[4], results_gbf[5])

                        optimal_load = max(results_gb[4], results_gbf[4])

                        if core == 1:
                            jobs = copy.deepcopy(jobs_master)
                            machines = copy.deepcopy(machines_master)
                            threshold = AlgorithmThreshold(jobs, machines, slack)
                            results_th = threshold.execute()
                            data += "{}; {}; {}; {}; {}; {}; ".format(results_th[0], results_th[1], results_th[2],
                                                                      results_th[3], results_th[4], results_th[5])
                            optimal_load = max(optimal_load, results_th[4])

                        if core == 30 or core == 120:
                            jobs = copy.deepcopy(jobs_master)
                            machines = copy.deepcopy(machines_master)
                            greedy_minidle = AlgorithmGMinIdle(jobs, machines)
                            results_gmi = greedy_minidle.execute()
                            data += "{}; {}; {}; {}; {}; {}; ".format(results_gmi[0], results_gmi[1], results_gmi[2],
                                                                      results_gmi[3], results_gmi[4], results_gmi[5])
                            optimal_load = max(optimal_load, results_gmi[4])

                        data += "{}; ".format(optimal_load)
                        print(data)

                        data += "\n"
                        with open(result_file, "a") as file:
                            file.write(data)
                        file.close()

        self.__operations.update_parallel_log(day, core, 'end')

    def run_specific_day_machine_limits(self, day, trace_id, core, slack_set, num):
        details = True
        file_name = "minimum_machines_c{}.txt".format(core)
        result_file = RESULT_FOLDER + file_name

        machines_n = []
        if core == 1:
            machine_start = MACHINE_START[trace_id][core]
            machine_end = machine_start * 100
            machines_n = [n for n in range(machine_start, machine_end, 50)]
        elif core == 30:
            machine_start = MACHINE_START[trace_id][core]
            machine_end = machine_start * 100
            machines_n = [n for n in range(machine_start, machine_end, 50)]
        elif core == 120:
            machine_start = MACHINE_START[trace_id][core]
            machine_end = machine_start * 100
            machines_n = [n for n in range(machine_start, machine_end, 50)]

        trace_jobs = self.__operations.read_jobs_iso(trace_id, day, core)

        total_load = 0
        for job in trace_jobs:
            total_load += job.get_processing_time() * job.get_job_core()

        print("Started for day {}.".format(day))
        if details:
            slack = 0.1
            standard_deviation = 0.05

            self.__operations.generate_statistical_trace_iso(trace_jobs, trace_id, day, core,
                                                             slack_set, slack, standard_deviation, num)

            job_file = self.__operations.get_statistical_trace_file_location(trace_id, day, slack, standard_deviation,
                                                                             core, num, True)

            jobs_master = self.__operations.get_jobs(job_file)

            start_idx = 0
            end_idx = len(machines_n) - 1

            counter = 0

            while start_idx != end_idx:
                mid_idx = math.ceil((start_idx + end_idx) / 2)
                machine = machines_n[int(mid_idx)]

                jobs = copy.deepcopy(jobs_master)
                machines = self.__operations.get_machines(machine)

                greedybalanced = AlgorithmGBalanced(jobs, machines)
                [accepted_jobs, rejected_jobs, accepted_load,
                 rejected_load, optimal_load, execution_time] = greedybalanced.execute()

                if accepted_load + rejected_load == optimal_load:
                    end_idx = mid_idx
                elif accepted_load + rejected_load > optimal_load:
                    start_idx = mid_idx

                if end_idx == start_idx + 1:
                    counter += 1

                if counter == 2:
                    break

            with open(result_file, "a") as file:
                data = "{} : {} : {}\n".format(day, len(jobs_master), machines_n[end_idx])
                file.write(data)
                print("Completed for day {}.".format(day))
            file.close()
