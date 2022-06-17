import sys

from functions import Operations
from algorithms import AlgorithmGBalanced, AlgorithmGBestFit, AlgorithmThreshold, AlgorithmGMinIdle
from settings import SETS, SLACKS, SD
from settings import STATISTICAL_TRACE_FOLDER, RESULT_FOLDER
import copy


class Scheduler:

    def __init__(self):
        self.__operations = Operations()

    def run_specific_day(self, day, trace_id, core, slack_set):
        trace_jobs = self.__operations.read_jobs_iso(trace_id, day, core)
        for num in SETS:
            result_file = RESULT_FOLDER + self.__operations.get_result_file_name(trace_id, day, core, num)
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

            for slack in SLACKS:
                for value in SD:

                    standard_deviation = round(slack/value, 3)
                    self.__operations.generate_statistical_trace_iso(trace_jobs, trace_id, day, core,
                                                                     slack_set, slack, standard_deviation, num)

                    job_file = self.__operations.get_statistical_trace_file_location(trace_id, day, slack,
                                                                                     standard_deviation, core, num,
                                                                                     True)
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

                        if core == 30:
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



    def run_specific_day_limits(self, day, trace_id, core, slack_set):
        trace_jobs = self.__operations.read_jobs_iso(trace_id, day, core)

        total_load = 0
        for job in trace_jobs:
            total_load += job.get_processing_time() * job.get_job_core()

        print("Total {} jobs available with load {}".format(len(trace_jobs), total_load))

        slack = 0.1
        standard_deviation = 0.05
        num = 1

        self.__operations.generate_statistical_trace_iso(trace_jobs, trace_id, day, core,
                                                         slack_set, slack, standard_deviation, num)

        job_file = self.__operations.get_statistical_trace_file_location(trace_id, day, slack, standard_deviation,
                                                                         core, num, True)

        jobs_master = self.__operations.get_jobs(job_file)

        for machine in range(300, 10000, 50):
            print("Started with day {} with machines {}".format(day, machine))
            jobs = copy.deepcopy(jobs_master)
            machines = self.__operations.get_machines(machine)

            greedybalanced = AlgorithmGBalanced(jobs, machines)
            [accepted_jobs, rejected_jobs, accepted_load, rejected_load, optimal_load] = greedybalanced.execute()

            if accepted_load + rejected_load == optimal_load:
                with open(RESULT_FOLDER + 'machinelimits3.txt', 'a') as file:
                    file.write("{} : {} : {}\n".format(day, len(jobs_master), machine))
                file.close()
                break











