import math
import sys
import os
import shutil

from datetime import datetime
from settings import CLOUD_TRACE_FOLDER, SLACK_FOLDER, STATISTICAL_TRACE_FOLDER
from settings import RESULT_FOLDER, LOG_FOLDER
from settings import RAW
from settings import TRACE, DAYS, SLACKS, SD, MI2011, SETS
from schedulingelements import Job, Machine
from settings import MACHINE_START, MACHINE_END, MACHINE_INCREMENT


class Operations:
    def __init__(self):
        pass

    # Methods available for external use

    # Read jobs from statistical trace file and returns them as a list
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

    # Initialize machines and return a list
    @staticmethod
    def get_machines(machine_num):
        machines = []
        for m in range(1, machine_num+1):
            machine = Machine(m)
            machines.append(machine)

        return machines

    # Generates statistical trace based on slack files and trace jobs
    # Can be generated for all days at once or all traces for a single day based on day_nr=None
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
    def read_jobs_iso(trace_id, day, core):
        # Started reading jobs - for particular day
        # Operations.update_system_log('Started reading jobs.')
        jobs = Operations.__get_jobs(trace_id, day, core)
        # Operations.update_system_log('Completed reading jobs.')
        return jobs

    # Generates statistical trace based on slack files and trace jobs, one file per simulation
    @staticmethod
    def generate_statistical_trace_iso(jobs, trace_id, day, core, slack_set, slack, standard_deviation, set_num):
        # Generate statistical trace file
        slacks = Operations.__get_lognormal_slacks(slack_set, slack, standard_deviation, set_num)
        file_location = Operations.__set_statistical_trace_file_location(core, day, True)
        statistical_trace_file = Operations.__get_statistical_trace_file_name(trace_id,
                                                                              day,
                                                                              slack,
                                                                              standard_deviation,
                                                                              core,
                                                                              set_num)
        print('Generating file ', statistical_trace_file)
        #Operations.update_system_log("Generating file {}".format(statistical_trace_file))
        file = open(file_location + statistical_trace_file, 'w')
        for job in jobs:
            release_time = job.get_release_time()
            processing_time = job.get_processing_time()
            epsilon = slacks.pop()
            due_time = math.ceil(release_time + (1 + epsilon) * processing_time)
            file.write(Operations.__get_csv_details(job, due_time, epsilon))
        file.close()

        print('Completed file ', statistical_trace_file)
        #Operations.update_system_log("Completed file {}".format(statistical_trace_file))
        #Operations.update_system_log('Completed trace generation')

    # Provides location of trace files based on simulation run type
    # single=False, when we have enough space and all traces are generated well in advance
    # single=True, when we generate trace for a day, run simulation and then clear it at the end
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
    def get_machine_settings(trace_id, day, core):
        machine_start = MACHINE_START[trace_id][core]
        machine_increment = MACHINE_INCREMENT[trace_id][core][day]
        machine_end = MACHINE_END[trace_id][core][day]

        return [machine_start, machine_end, machine_increment]

    @staticmethod
    def get_result_file_name(trace_id, day, core, set_num):
        file = 'Result' + trace_id + \
               'L60D' + str(day) + \
               'C' + str(core) + \
               'S' + str(set_num) + \
               ".txt"
        return file

    # LOG FILE METHODS
    # Creates an entry into the main simulation log
    @staticmethod
    def update_system_log(algorithm_id, job_num, machine_num, execution_time, reset=False):
        file_location = LOG_FOLDER + 'simulationlog.txt'
        if reset:
            file = open(file_location, 'w')
        else:
            file = open(file_location, 'a')

        stamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        data = "{} simulation with {} jobs on {} machines, "\
               "finished execution in {} seconds.".format(algorithm_id,
                                                          job_num,
                                                          machine_num,
                                                          execution_time)
        file.write("{} \t {}\n".format(stamp, data))
        file.close()

    @staticmethod
    def update_parallel_log(day, core, action):
        file_location = LOG_FOLDER + 'parallellog.txt'
        file = open(file_location, 'a')
        stamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        data = "{} \t {} for day {} for jobs with cores {}.\n".format(action.upper(), stamp, day, core)
        file.write(data)
        file.close()

    @staticmethod
    def update_time_log(algorithm_id, job_num, machine_num, execution_time, reset=False):
        file_location = LOG_FOLDER + 'timelog.txt'
        if reset:
            file = open(file_location, 'w')
        else:
            file = open(file_location, 'a')

        stamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        data = "{}; {}; {}; {}".format(algorithm_id,
                                       job_num,
                                       machine_num,
                                       execution_time)
        file.write("{} \t {}\n".format(stamp, data))
        file.close()

    # Creates and entry into the algorithm log
    @staticmethod
    def update_algorithm_log(algorithm_id, job_num, machine_num, execution_time, reset=False):
        file_folder = LOG_FOLDER + algorithm_id + '/'
        if not os.path.exists(file_folder):
            os.makedirs(file_folder)
        file_location = file_folder + 'runtime.txt'
        if reset:
            file = open(file_location, 'w')
        else:
            file = open(file_location, 'a')

        stamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        data = "{}; {}; {};".format(job_num, machine_num, execution_time)
        file.write("{} \t {}\n".format(stamp, data))
        file.close()

    @staticmethod
    def update_machine_log(algorithm_id, machines):
        file_folder = LOG_FOLDER + algorithm_id + '/'
        if not os.path.exists(file_folder):
            os.makedirs(file_folder)
        file_location = file_folder + 'machinelog.txt'
        file = open(file_location, 'w')

        stamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        for machine in machines:
            file.write("{} \t {}\n".format(stamp, machine.get_schedule()))
        file.close()

    @staticmethod
    def update_job_log(algorithm_id, accepted_jobs, rejected_jobs):
        file_folder = LOG_FOLDER + algorithm_id + '/'
        if not os.path.exists(file_folder):
            os.makedirs(file_folder)
        file_location = file_folder + 'joblog.txt'
        file = open(file_location, 'w')

        stamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        jobs = accepted_jobs + rejected_jobs
        for job in jobs:
            file.write("{} \t {}\n".format(stamp, job.get_stat()))
        file.close()

    @staticmethod
    def clear_all_logs():
        contents = []
        if os.path.exists(LOG_FOLDER):
            contents = os.listdir(LOG_FOLDER)

        while len(contents) > 0:
            content = contents.pop()
            if os.path.isfile(os.path.join(LOG_FOLDER, content)):
                if content != 'README':
                    os.remove(os.path.join(LOG_FOLDER, content))
            elif os.path.isdir(os.path.join(LOG_FOLDER, content)):
                shutil.rmtree(os.path.join(LOG_FOLDER, content))

    @staticmethod
    def clear_all_results():
        contents = []
        if os.path.exists(RESULT_FOLDER):
            contents = os.listdir(RESULT_FOLDER)

        while len(contents) > 0:
            content = contents.pop()
            if os.path.isfile(os.path.join(RESULT_FOLDER, content)):
                if content != 'README':
                    os.remove(os.path.join(RESULT_FOLDER, content))
            elif os.path.isdir(os.path.join(RESULT_FOLDER, content)):
                shutil.rmtree(os.path.join(RESULT_FOLDER, content))

    @staticmethod
    def clear_all_trace_files():
        contents = []
        if os.path.exists(STATISTICAL_TRACE_FOLDER):
            contents = os.listdir(STATISTICAL_TRACE_FOLDER)

        while len(contents) > 0:
            content = contents.pop()
            if os.path.isfile(os.path.join(STATISTICAL_TRACE_FOLDER, content)):
                if content != 'README':
                    os.remove(os.path.join(STATISTICAL_TRACE_FOLDER, content))
            elif os.path.isdir(os.path.join(STATISTICAL_TRACE_FOLDER, content)):
                shutil.rmtree(os.path.join(STATISTICAL_TRACE_FOLDER, content))

        os.makedirs(os.path.join(STATISTICAL_TRACE_FOLDER,'runningtrace'))

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
            file_location = STATISTICAL_TRACE_FOLDER + 'runningtrace/'

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

            if job_core <= core and job_category.lower().__eq__('accept'):
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










