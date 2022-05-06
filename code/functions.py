import math
import sys
import os

from datetime import datetime
from settings import CLOUD_TRACE_FOLDER, SLACK_FOLDER, STATISTICAL_TRACE_FOLDER
from settings import RESULT_FOLDER, LOG_FOLDER
from settings import RAW
from settings import TRACE, DAYS, SLACKS, SD, MI2011, SETS
from schedulingelements import Job, Machine


class Operations:
    def __init__(self):
        pass

    @staticmethod
    def get_jobs(job_file):
        with open(job_file) as file:
            contents = file.readlines()

        jobs = []
        for data in contents:
            job_data = data.strip().split(';')
            job = Job(job_data[0], int(job_data[1]), int(job_data[2]), int(job_data[3]), int(job_data[4]))
            jobs.append(job)

        return jobs

    @staticmethod
    def get_machines(machine_num):
        machines = []
        for m in range(1, machine_num+1):
            machine = Machine(m)
            machines.append(machine)

        return machines

    @staticmethod
    def generate_statistical_trace(trace_id, slack_set, core, day_nr=None):
        if not day_nr:
            period = DAYS[trace_id]
            single = False
        else:
            period = [day_nr]
            single = True

        # generate trace
        Operations.update_system_log('Started trace generation.')
        for day in period:
            jobs = Operations.__get_jobs(trace_id, day, core)
            for num in SETS:
                for slack in SLACKS:
                    for value in SD:
                        standard_deviation = round(slack/value, 3)
                        slacks = Operations.__get_lognormal_slacks(slack_set, slack, standard_deviation, num)
                        file_location = Operations.__set_statistical_trace_file_location(core, day, single)
                        statistical_trace_file = Operations.__get_statistical_trace_file_name(trace_id,
                                                                                              day,
                                                                                              slack,
                                                                                              standard_deviation,
                                                                                              core,
                                                                                              num)
                        print('Generating file ', statistical_trace_file)
                        Operations.update_system_log("Generating file {}".format(statistical_trace_file))
                        file = open(file_location + statistical_trace_file, 'w')
                        for job in jobs:
                            release_time = job.get_release_time()
                            processing_time = job.get_processing_time()
                            epsilon = slacks.pop()
                            due_time = math.ceil(release_time + (1 + epsilon) * processing_time)
                            file.write(Operations.__get_csv_details(job, due_time, epsilon))
                        file.close()
                        Operations.update_system_log("Completed file {}".format(statistical_trace_file))
        Operations.update_system_log('Completed trace generation')

    @staticmethod
    def get_statistical_trace_file_location(trace_id, day, slack, standard_deviation, core, set_num, single=False):
        file_directory = Operations.__set_statistical_trace_file_location(core, day, single)
        file_name = Operations.__get_statistical_trace_file_name(trace_id,
                                                                 day,
                                                                 slack,
                                                                 standard_deviation,
                                                                 core,
                                                                 set_num)
        file_path = file_directory + file_name
        if not os.path.exists(file_path):
            print('File does not exist!')
            sys.exit()

        return file_path

    @staticmethod
    def update_system_log(data, reset=False):
        file_location = LOG_FOLDER + 'simulation-log.txt'
        if reset:
            file = open(file_location, 'w')
        else:
            file = open(file_location, 'a')

        stamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        file.write("{} \t {}\n".format(stamp, data))

    @staticmethod
    def update_algorithm_log(algorithm_id, data, reset=False):
        file_location = LOG_FOLDER + algorithm_id + '.txt'
        if reset:
            file = open(file_location, 'w')
        else:
            file = open(file_location, 'a')

        stamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        file.write("{} \t {}\n".format(stamp, data))

    @staticmethod
    def get_machine_limit(jobs):
        pass

    @staticmethod
    def __get_trace_file_name(trace_id, day):
        file = RAW[trace_id] + \
               'D' + str(day) + \
               '.txt'
        return file

    @staticmethod
    def __get_statistical_trace_file_name(trace_id, day, slack, standard_deviation, core, set_num):
        file = TRACE[trace_id] + \
               'D' + str(day) + \
               'L60M' + str(slack) + \
               'SD' + str(standard_deviation) + \
               'C' + str(core) + \
               'S' + str(set_num) + \
               ".txt"
        return file

    @staticmethod
    def __set_statistical_trace_file_location(core, day, single=False):
        file_location = STATISTICAL_TRACE_FOLDER + 'all-traces/c' + str(core) + '/' + 'day' + str(day) + '/'
        if single:
            file_location = STATISTICAL_TRACE_FOLDER + 'running-trace/'

        if not os.path.exists(file_location):
            os.makedirs(file_location)

        return file_location

    @staticmethod
    def __get_lognormal_slack_file_name(slack, standard_deviation, set_num):
        file = 'LognormalS' + \
               'M' + str(slack) + \
               'SD' + str(standard_deviation) + \
               'S' + str(set_num) + \
               ".txt"
        return file

    @staticmethod
    def __get_lognormal_slacks(slack_set, slack, standard_deviation, set_num):
        file_name = Operations.__get_lognormal_slack_file_name(slack, standard_deviation, set_num)
        slack_file = SLACK_FOLDER[slack_set] + file_name
        with open(slack_file) as file:
            contents = file.readlines()

        slacks = []
        for data in contents:
            slacks.append(float(data.strip()))

        return slacks

    @staticmethod
    def __get_jobs(trace_id, day, core):
        file_name = Operations.__get_trace_file_name(trace_id, day)
        trace_file = CLOUD_TRACE_FOLDER[trace_id] + file_name
        with open(trace_file) as file:
            contents = file.readlines()

        jobs = []
        for data in contents:
            job_data = data.strip().split('\t')
            job_core = int(job_data[11])
            job_category = job_data[10]

            if job_core == core and job_category.lower().__eq__('accept'):
                job_id = job_data[0]
                processing_time = int(job_data[3])
                release_time = int(job_data[8])
                due_time = 0
                job = Job(job_id, processing_time, release_time, due_time, job_core)
                jobs.append(job)
        return jobs

    @staticmethod
    def __get_csv_details(job, due_time, slack):
        return ("{};{};{};{};{};{};\n".format(job.get_job_id(),
                                              job.get_processing_time(),
                                              job.get_release_time(),
                                              due_time,
                                              job.get_job_core(),
                                              slack))


class Simulation:

    def __init__(self):
        pass

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













