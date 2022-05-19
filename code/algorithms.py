import os
import sys
import time
import math
import numpy as np
from functions import Operations
from settings import RESULT_FOLDER
from schedulingelements import Job, Container, Machine


class Algorithm:
    def __init__(self, algorithm_id, jobs, machines, trial=False):
        # algorithm class variables - jobs, which hold submitted jobs
        # machines, hold machines in their initial state, where all are available at time 0
        self.__jobs = jobs
        self.__machines = machines

        # id holds the unique identifier for a particular algorithm
        self.__id = algorithm_id
        # various operations like reading job, initializing machine, updating logs are in Operations class
        self.__operations = Operations()
        # total number of jobs submitted
        self.__job_num = len(jobs)
        # total number of machines in the set-up
        self.__machine_num = len(machines)
        # time taken to completely execute n jobs on m machines
        self.__execution_time = None

        # list of containers which are deployed. each container holds a single job
        self.__containers = []
        # list of accepted and rejected jobs
        self.__accepted_jobs = []
        self.__rejected_jobs = []
        # total load, number of cores * processing time of a job
        self.__accepted_load = 0
        self.__rejected_load = 0
        # it is either the total submitted load or number of cores * makespan
        self.__optimal_load = 0

        self.__trial_mode = trial

    # Get methods to access private class variables
    def get_job_list(self):
        return self.__jobs

    def get_job_fifo(self):
        return self.__jobs.pop(0)

    def get_machine_list(self):
        return self.__machines

    def get_machine_num(self):
        return self.__machine_num

    def get_rejected_jobs(self):
        return self.__rejected_jobs

    # Update methods to modify private class variables
    def update_machine(self, core, container, completion_time):
        self.__machines[core].update(container, completion_time)

    def update_container_list(self, container):
        self.__containers.append(container)

    def update_accepted(self, job):
        self.__accepted_jobs.append(job)
        self.__accepted_load += job.get_job_core() * job.get_processing_time()

    def update_rejected(self, job):
        self.__rejected_jobs.append(job)
        self.__rejected_load += job.get_job_core() * job.get_processing_time()

    def update_execution_time(self, time):
        self.__execution_time = time

    # Returns result in a list form
    # n_accepted jobs, n_rejected_jobs, accepted load, rejected load, optimal load
    def _results(self):
        self.__machines.sort(key=lambda m:m.get_available_time(), reverse=True)
        makespan = self.__machines[0].get_available_time()
        total_resources = len(self.__machines) * makespan
        total_load = self.__accepted_load + self.__rejected_load
        self.__optimal_load = min(total_resources, total_load)
        return ([len(self.__accepted_jobs), len(self.__rejected_jobs),
                 self.__accepted_load, self.__rejected_load, self.__optimal_load])

    # method to sort jobs in ascending order of their release times
    def _sort_jobs_ascending_release_time(self):
        self.__jobs.sort(key=lambda j:j.get_release_time())

    # method to sort machines so that most loaded stays on top and least loaded at the bottom
    def _sort_machines_descending_avail_time(self):
        self.__machines.sort(key=lambda m:m.get_available_time(), reverse=True)

    # method to return start time of a particular job on a particular machine
    def _get_start_time(self, job, core):
        release_time = job.get_release_time()
        machine_avail_time = self.__machines[core].get_available_time()

        start_time = max(machine_avail_time, release_time)
        return start_time

    # method to return completion time of a job on a particular machine
    def _get_completion_time(self, job, core):
        release_time = job.get_release_time()
        processing_time = job.get_processing_time()
        machine_avail_time = self.__machines[core].get_available_time()

        completion_time = max(machine_avail_time, release_time) + processing_time
        return completion_time

    # logarithmic search method to find the index of the most loaded machine, where job can be completed legally
    def _search_loaded_machine(self, job):
        # If the job can be scheduled legally on the most loaded machine, then we go ahead with it
        if self._get_completion_time(job, 0) <= job.get_due_time():
            return 0
        else:
            # We use logarithmic search to arrive at the number of machines
            m_upper = 0
            m_lower = self.__machine_num - 1

            # if both are the same, then we only have one machine
            if m_upper == m_lower:
                return m_upper

            # if there are more than one machine, then we search for the most loaded one
            count = 0
            while m_upper != m_lower:
                m = math.ceil((m_upper + m_lower) / 2)
                # there are only 2 machines. if first machine was capable of hosting the job, initial check
                # returned 0. so we return the second machine
                if m == m_lower:
                    return m_lower

                # in case of more than 2 machines, we keep shifting limits
                if self._get_completion_time(job, m) <= job.get_due_time():
                    m_lower = m
                else:
                    m_upper = m

            # upon both limits converging, we return the machine index
            return m_lower

    # method which updates individual simulation logs for future reference
    def _update_logs(self):
        if not self.__trial_mode:
            self.__operations.update_system_log(self.__id, self.__job_num, self.__machine_num, self.__execution_time)
            self.__operations.update_time_log(self.__id, self.__job_num, self.__machine_num, self.__execution_time)
            self.__operations.update_algorithm_log(self.__id, self.__job_num, self.__machine_num, self.__execution_time)
            self.__operations.update_machine_log(self.__id, self.__machines)
            self.__operations.update_job_log(self.__id, self.__accepted_jobs, self.__rejected_jobs)


class AlgorithmGBalanced(Algorithm):
    """
        this class basically inherits all properties of the Algorithm class.
        here if a job can be legally scheduled on the least loaded machine, then we accept it.
        we schedule the job on that particular machine.
        in case of multicore jobs, we only consider machines {1, ..., m - core + 1} to check feasibility.
    """

    def __init__(self, jobs, machines):
        super().__init__('greedybalanced', jobs, machines)

    def execute(self, trial=False):
        container_id = 1
        simulation_start_time = time.time()
        super()._sort_jobs_ascending_release_time()
        while len(super().get_job_list()) > 0:
            job = super().get_job_fifo()

            # Sort machines based on reverse order of remaining load
            super()._sort_machines_descending_avail_time()

            # Check whether the job can be legally completed
            # Considering multi-core jobs, last core for job c = m - job_core
            start_core = super().get_machine_num() - job.get_job_core()
            if start_core < 0:
                super().update_rejected(job)
                continue

            start_time = super()._get_start_time(job, start_core)
            completion_time = super()._get_completion_time(job, start_core)
            if completion_time <= job.get_due_time():
                for core in range(start_core, super().get_machine_num()):
                    container = Container(container_id)
                    container.assign(job, start_time, completion_time,
                                     super().get_machine_list()[core].get_machine_id())

                    super().update_machine(core, container, completion_time)
                    super().update_container_list(container)
                    container_id += 1

                job.update(start_time, completion_time)
                super().update_accepted(job)
            else:
                super().update_rejected(job)
        simulation_end_time = time.time()
        execution_time = round(simulation_end_time - simulation_start_time, 4)
        super().update_execution_time(execution_time)

        super()._update_logs()
        return super()._results()


class AlgorithmGBestFit(Algorithm):
    """
        this class basically inherits all properties of the Algorithm class.
        here if a job can be legally scheduled on the least loaded machine, then we accept it.
        we schedule the job on the first most loaded machine, that can complete the job on or before its deadline.
        in case of multicore jobs, we only consider machines {1, ..., m - core + 1} to check feasibility.
    """

    def __init__(self, jobs, machines):
        super().__init__('greedybestfit', jobs, machines)

    def execute(self, trial=False):
        container_id = 1
        simulation_start_time = time.time()
        super()._sort_jobs_ascending_release_time()
        while len(super().get_job_list()) > 0:
            job = super().get_job_fifo()

            # Sort machines based on reverse order of remaining load
            super()._sort_machines_descending_avail_time()

            # Check whether the job can be legally completed
            # Considering multi-core jobs, last core for job c = m - job_core
            start_core = super().get_machine_num() - job.get_job_core()
            if start_core < 0:
                super().update_rejected(job)
                continue

            start_time = super()._get_start_time(job, start_core)
            completion_time = super()._get_completion_time(job, start_core)
            if completion_time <= job.get_due_time():
                start_core = super()._search_loaded_machine(job)
                start_time = super()._get_start_time(job, start_core)
                completion_time = super()._get_completion_time(job, start_core)
                for core in range(start_core, start_core + job.get_job_core()):
                    container = Container(container_id)
                    container.assign(job, start_time, completion_time,
                                     super().get_machine_list()[core].get_machine_id())
                    super().update_machine(core, container, completion_time)
                    super().update_container_list(container)
                    container_id += 1

                job.update(start_time, completion_time)
                super().update_accepted(job)
            else:
                super().update_rejected(job)

        simulation_end_time = time.time()
        execution_time = round(simulation_end_time - simulation_start_time, 4)
        super().update_execution_time(execution_time)

        super()._update_logs()
        return super()._results()


class AlgorithmThreshold(Algorithm):
    """
        this class basically inherits all properties of the Algorithm class.
        first we calculate the deadline threshold and compare it with due date of the job.
        if the due date is less than the deadline threshold, then we reject it immediately.
        if not, then we consider the job and check whether we can schedule it legally.
        if the job can be legally scheduled on the least loaded machine, then we accept it.
        we schedule the job on the first most loaded machine, that can complete the job on or before its deadline.
        in case of multicore jobs, we only consider machines {1, ..., m - core + 1} to check feasibility.
    """

    def __init__(self, jobs, machines, epsilon):
        super().__init__('threshold', jobs, machines)
        self.__epsilon = epsilon

    def execute(self):
        container_id = 1
        simulation_start_time = time.time()
        super()._sort_jobs_ascending_release_time()
        f_values = self.__calculate_f_values_epsilon()

        n = 1
        while len(super().get_job_list()) > 0:
            job = super().get_job_fifo()
            n += 1
            deadline_threshold = self.__calculate_deadline_threshold(f_values, job)

            if job.get_due_time() < deadline_threshold:
                super().update_rejected(job)
            else:
                start_core = super().get_machine_num() - job.get_job_core()
                if start_core < 0:
                    super().update_rejected(job)
                    continue

                completion_time = super()._get_completion_time(job, start_core)
                if completion_time <= job.get_due_time():
                    start_core = super()._search_loaded_machine(job)
                    start_time = super()._get_start_time(job, start_core)
                    completion_time = super()._get_completion_time(job, start_core)
                    for core in range(start_core, start_core + job.get_job_core()):
                        container = Container(container_id)
                        container.assign(job, start_time, completion_time,
                                         super().get_machine_list()[core].get_machine_id())
                        super().update_machine(core, container, completion_time)
                        super().update_container_list(container)
                        container_id += 1

                    job.update(start_time, completion_time)
                    super().update_accepted(job)
                else:
                    super().update_rejected(job)

        simulation_end_time = time.time()
        execution_time = round(simulation_end_time - simulation_start_time, 4)
        super().update_execution_time(execution_time)

        super()._update_logs()
        return super()._results()

    def __calculate_f_value_limits(self):
        machine_num = super().get_machine_num()
        f_eps_m_k = np.zeros((machine_num + 1, machine_num + 1))
        f_eps_m_k_limits = np.zeros((machine_num, 2))

        for m in range(1, machine_num):
            k = machine_num - m
            f_eps_m_k[m, k] = 2.0
            left_value = (machine_num * f_eps_m_k[m, k] + 1) / k

            for q in range(k + 1, machine_num + 1):
                denominator = k
                for h in range(k, q):
                    denominator = denominator + f_eps_m_k[m, h] - 1
                f_eps_m_k[m, q] = (left_value * denominator - 1) / machine_num
                f_eps_m_k_limits[m - 1, 0] = f_eps_m_k[m, k]
                f_eps_m_k_limits[m - 1, 1] = f_eps_m_k[m, q]
                break

        f_eps_m_k_limits[machine_num - 1, 0] = 2.0
        f_eps_m_k_limits[machine_num - 1, 1] = 5.0
        # This function returns the f_value matrix

        return f_eps_m_k_limits

    def __calculate_eps_value(self, k, f_value):
        machine_num = super().get_machine_num()
        f_eps_m_k = np.zeros(machine_num + 1)
        f_eps_m_k[k] = f_value
        left_value = (machine_num * f_eps_m_k[k] + 1) / k

        for q in range(k + 1, machine_num + 1):
            denominator = k
            for h in range(k, q):
                denominator = denominator + f_eps_m_k[h] - 1
            f_eps_m_k[q] = (left_value * denominator - 1) / machine_num

        epsilon_value = 1 / (f_eps_m_k[machine_num] - 1)
        f_eps_m_k[0] = epsilon_value
        return f_eps_m_k

    def __calculate_f_values_epsilon(self):
        machine_num = super().get_machine_num()
        f_eps_m_k_limits = self.__calculate_f_value_limits()
        row, col = f_eps_m_k_limits.shape
        for i in range(0, row):
            f_value_i_lower_limit = f_eps_m_k_limits[i, 0]
            f_value_i_upper_limit = f_eps_m_k_limits[i, 1]

            k = machine_num - i

            eps_value_i_lower_limit = self.__calculate_eps_value(k, f_value_i_lower_limit)
            eps_value_i_upper_limit = self.__calculate_eps_value(k, f_value_i_upper_limit)
            eps_value_i_mid = []

            lower_eps_value = eps_value_i_upper_limit[0]
            upper_eps_value = eps_value_i_lower_limit[0]
            mid_eps_value = 99999

            if lower_eps_value <= self.__epsilon <= upper_eps_value:
                while mid_eps_value != self.__epsilon:
                    f_value_i_mid = (f_value_i_lower_limit + f_value_i_upper_limit) / 2

                    eps_value_i_lower_limit = self.__calculate_eps_value(k, f_value_i_lower_limit)
                    eps_value_i_upper_limit = self.__calculate_eps_value(k, f_value_i_upper_limit)
                    eps_value_i_mid = self.__calculate_eps_value(k, f_value_i_mid)

                    lower_eps_value = eps_value_i_upper_limit[0]
                    upper_eps_value = eps_value_i_lower_limit[0]
                    mid_eps_value = eps_value_i_mid[0]

                    if mid_eps_value >= self.__epsilon >= lower_eps_value:
                        f_value_i_lower_limit = f_value_i_mid
                    elif mid_eps_value <= self.__epsilon <= upper_eps_value:
                        f_value_i_upper_limit = f_value_i_mid

                    if round(mid_eps_value, 13) == float(self.__epsilon):
                        break

                return eps_value_i_mid

    def __calculate_deadline_threshold(self, f_values, job):
        # This function calculates the maximum deadline threshold
        # First sort the machines in descending order
        release_time = job.get_release_time()
        super()._sort_machines_descending_avail_time()
        # Calculate deadline threshold of individual machines
        deadline_threshold_m = []
        for m in range(0, super().get_machine_num()):
            load_m = super().get_machine_list()[m].get_available_time() - release_time
            deadline_threshold_m.append(release_time + load_m * f_values[m + 1])
        # Return the maximum value
        return max(deadline_threshold_m)


class AlgorithmGMinIdle(Algorithm):
    """
        this class basically inherits all properties of the Algorithm class.
        this algorithm aims to minimize the total block created by the jobs scheduled.
        first, we check whether we can schedule the job legally.
        if yes, we accept it.
        we then go through all machines on which the job can be scheduled and calculate the block time.
        we select the cores, which are least blocked by this job and schedule the job.
        in case of multicore jobs, we only consider machines {1, ..., m - core + 1} to check feasibility.
    """
    def __init__(self, jobs, machines):
        super().__init__('greedyminidle', jobs, machines)

    def execute(self, trial=False):
        container_id = 1
        simulation_start_time = time.time()
        super()._sort_jobs_ascending_release_time()
        while len(super().get_job_list()) > 0:
            job = super().get_job_fifo()

            # Sort machines based on reverse order of remaining load
            super()._sort_machines_descending_avail_time()

            # Check whether the job can be legally completed
            # Considering multicore jobs, last core for job c = m - job_core
            start_core = super().get_machine_num() - job.get_job_core()
            if start_core < 0:
                super().update_rejected(job)
                continue

            completion_time = super()._get_completion_time(job, start_core)
            if completion_time <= job.get_due_time():
                minimum_idle_time = None
                minimum_idle_core = None
                for start_core in range(0, super().get_machine_num() - job.get_job_core() + 1):
                    completion_time = super()._get_completion_time(job, start_core)
                    if completion_time <= job.get_due_time():
                        start_time = super()._get_start_time(job, start_core)
                        total_idle_time = 0
                        for core in range(start_core, start_core + job.get_job_core()):
                            total_idle_time += start_time - super().get_machine_list()[core].get_available_time()

                        if minimum_idle_core is None:
                            minimum_idle_time = total_idle_time
                            minimum_idle_core = start_core

                        if minimum_idle_time > total_idle_time:
                            minimum_idle_time = total_idle_time
                            minimum_idle_core = start_core

                if minimum_idle_core is None:
                    print("ERROR: Valid core not found!")
                    sys.exit()

                start_time = super()._get_start_time(job, minimum_idle_core)
                completion_time = super()._get_completion_time(job, minimum_idle_core)
                for core in range(minimum_idle_core, minimum_idle_core + job.get_job_core()):
                    container = Container(container_id)
                    container.assign(job, start_time, completion_time,
                                     super().get_machine_list()[core].get_machine_id())
                    super().update_machine(core, container, completion_time)
                    super().update_container_list(container)
                    container_id += 1

                job.update(start_time, completion_time)
                super().update_accepted(job)
            else:
                super().update_rejected(job)

        simulation_end_time = time.time()
        execution_time = round(simulation_end_time - simulation_start_time, 4)
        super().update_execution_time(execution_time)

        super()._update_logs()
        return super()._results()


class AlgorithmBF(Algorithm):

    def __init__(self, algorithm_id, jobs, machines):
        super().__init__(algorithm_id, jobs, machines)
        self.__open_containers = []

    def get_open_containers(self):
        return self.__open_containers


class AlgorithmGBalancedBF:

    def __init__(self):
        pass

class AlgorithmGBestFitBF:

    def __init__(self):
        pass
