import copy
import os
import sys
import time
import math
import numpy as np
import copy as cp
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

        # container id variable
        self.__container_id = 1
        # list of containers which are deployed. each container holds a single job
        self.__containers = []
        # list of open containers - used based on type of algorithm
        self.__open_containers = []
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

    def get_accepted_jobs(self):
        return self.__accepted_jobs

    def get_rejected_jobs(self):
        return self.__rejected_jobs

    def get_open_containers(self):
        return self.__open_containers

    # Update methods to modify private class variables
    def update_machine(self, core, container, completion_time):
        self.__machines[core].update(container, completion_time)

    def update_container_list(self, container):
        self.__containers.append(container)

    def update_open_container_list_add(self, container):
        self.__open_containers.append(container)

    def update_open_container_list_pop(self, index):
        self.__open_containers.pop(index)

    def update_accepted(self, job):
        self.__accepted_jobs.append(job)
        self.__accepted_load += job.get_job_core() * job.get_processing_time()

    def update_rejected(self, job):
        self.__rejected_jobs.append(job)
        self.__rejected_load += job.get_job_core() * job.get_processing_time()

    def update_execution_time(self, execution_time):
        self.__execution_time = execution_time

    def allocate_job_to_core(self, job, start_core):
        # start time on this core
        start_time = self._get_start_time(job, start_core)
        # completion time on this core
        completion_time = self._get_completion_time(job, start_core)
        for core in range(start_core, start_core + job.get_job_core()):
            # storing initial machine available time for idle containers
            machine_available_time = self._get_machine_avail_time(core)
            # get machine id
            machine_id = self.get_machine_list()[core].get_machine_id()
            # generating container and assigning job to this container
            container = Container(self.__container_id)
            container.assign(job, start_time, completion_time, machine_id)
            # updating machine with this container
            self.update_machine(core, container, completion_time)
            # updating master container list
            self.update_container_list(container)
            # incrementing container number by 1
            self.__container_id += 1
            # only if the current job creates an idle slot on this machine, do
            if start_time - machine_available_time > 0:
                container = Container(self.__container_id)
                container.reserve(machine_available_time, start_time, start_time - machine_available_time, machine_id)
                self.update_open_container_list_add(container)
                self.__container_id += 1

        # updating job with start time and completion time
        job.update(start_time, completion_time)
        # updating the accepted jobs list
        self.update_accepted(job)

    def check_and_allocate_backfill(self, job):
        # if there are no open containers yet, simply return false
        if len(self.__open_containers) <= 0:
            # print('No open containers yet.')
            return False
        # get the job properties
        job_release_time = job.get_release_time()
        job_due_time = job.get_due_time()
        job_processing_time = job.get_processing_time()
        job_core = job.get_job_core()

        # create a binary matrix with eligible open containers
        container_bin_matrix = []
        # collect machines ids to which each container belongs
        container_machine_ids = []
        # for every container in the list of open containers, do
        for container in self.__open_containers:
            # time at which container becomes available
            container_start_time = container.get_start_time()
            # time after which the container is no longer available
            container_end_time = container.get_end_time()
            # usable length within the container w.r.t. our job
            usable_length = min(job_due_time, container_end_time) - max(job_release_time, container_start_time)
            # if we have enough space inside the container, do
            if usable_length >= job_processing_time:
                # first column is a reference to the container
                container_id = np.array([container.get_id()])
                # collect machine id
                container_machine_ids.append(container.get_machine())
                # each row is divided into three blocks
                # start block is vacant area from job release till container start, filled with zeros
                start_block = np.zeros(max(job_release_time, container_start_time) - job_release_time)
                # start block is vacant area from container end till job due, filled with zeros
                end_block = np.zeros(job_due_time - min(job_due_time, container_end_time))
                # mid block is the usable length of the container, filled with ones
                mid_block = np.ones(usable_length)
                # the appended row for the particular container
                container_bin_matrix.append(np.hstack((container_id, start_block, mid_block, end_block)))

        # if not even one container exists, where enough job length is available, then return false
        # else if containers are available partially, check for enough machines which are free
        free_machines = []
        if len(container_bin_matrix) <= 0:
            # print('Not even one open container exists, which has free space equivalent to the job length.')
            return False

        # this matrix sums up the rows vertically. if this value is larger than or equal to the job core requirement,
        # then we know that there are enough free containers at this point which meet the core requirement
        container_overlap_matrix = np.sum(container_bin_matrix, axis=0)

        # now we need to check whether there are enough overlapping containers to schedule our job
        start_point = None
        job_length = 0
        for position, value in enumerate(container_overlap_matrix):
            # we ignore the container id at this point
            if position == 0:
                continue
            # if we have enough containers, we take the current point as start point
            if value >= job_core:
                if start_point is None:
                    start_point = position
                job_length += 1
            else:
                # before covering the job length, if number drops - then we need to look for a new point
                start_point = None
                job_length = 0
            # if we found continuous job length in containers, then we are done
            if job_length == job_processing_time:
                break

        if start_point is None or job_length < job_processing_time:
            # print('Not enough containers to meet the core requirement of the job.')
            return False

        # variable to keep count of how many containers we already assigned
        assigned_containers = 0
        # variable hold the container ids in the current order of open containers
        container_ids = np.array([container.get_id() for container in self.__open_containers])
        # variable to hold containers, to which job has been allocated
        allocated_containers = []
        # variable holds new open containers, which might have been created because of job allocation
        open_containers_new = []
        # reference to original open container list, which need to be deleted because of new allocation
        delete_ids = []

        # go through each row of container binary matrix and allocate containers one by one
        for row in container_bin_matrix:
            # if enough job length is available in this container, then allocate job
            if row[start_point] == 1 and row[start_point + job_processing_time - 1] == 1:
                # get the container id
                container_id = row[0]
                # add container id to delete list
                delete_ids.append(container_id)

                # find the location of the container in the original list
                index_array = np.where(container_ids == container_id)
                index = index_array[0][0]
                # start and end times of the job, if assigned to this container
                job_start_time = job_release_time + start_point - 1
                job_end_time = job_start_time + job_processing_time
                machine_id = self.__open_containers[index].get_machine()
                # create a new container and assign to allocated list
                container = Container(self.__container_id)
                container.assign(job, job_start_time, job_end_time, machine_id)
                allocated_containers.append(container)
                self.__container_id += 1

                # if container is not fully utilized, there will still be idle slots
                # creating new open container, if idle slot precedes the allocated slot
                if job_start_time > self.__open_containers[index].get_start_time():
                    container = Container(self.__container_id)
                    # the container lies between earlier container start time and actual job start time
                    container.reserve(self.__open_containers[index].get_start_time(),
                                      job_start_time,
                                      job_start_time - self.__open_containers[index].get_start_time(),
                                      self.__open_containers[index].get_machine())
                    open_containers_new.append(container)
                    self.__container_id += 1

                # creating new open container, if idle slot follows the allocated slot
                if job_end_time < self.__open_containers[index].get_end_time():
                    container = Container(self.__container_id)
                    # the container lies between actual job end time and earlier container end time
                    container.reserve(job_end_time,
                                      self.__open_containers[index].get_end_time(),
                                      self.__open_containers[index].get_end_time() - job_end_time,
                                      self.__open_containers[index].get_machine())
                    open_containers_new.append(container)
                    self.__container_id += 1

                assigned_containers += 1

                # if enough containers are assigned for the job, then exit
                if assigned_containers == job_core:
                    job.update(job_start_time, job_end_time)
                    self.__accepted_jobs.append(job)
                    break

        _, indices, _ = np.intersect1d(container_ids, delete_ids, return_indices=True)
        indices = np.sort(indices)
        while len(indices) > 0:
            index = indices[-1]
            self.__open_containers.pop(index)
            indices = np.delete(indices, -1)

        for container in open_containers_new:
            self.__open_containers.append(cp.deepcopy(container))

        machine_ids = np.array([machine.get_machine_id() for machine in self.__machines])
        while len(allocated_containers) > 0:
            container = allocated_containers.pop(0)
            machine_id = container.get_machine()
            index_array = np.where(machine_ids == machine_id)
            index = index_array[0][0]
            self.__machines[index].attach(container)

        self.update_accepted(job)
        return True

    # Returns result in a list form
    # n_accepted jobs, n_rejected_jobs, accepted load, rejected load, optimal load
    def _results(self):
        self.__machines.sort(key=lambda m: m.get_available_time(), reverse=True)
        makespan = self.__machines[0].get_available_time()
        total_resources = len(self.__machines) * makespan
        total_load = self.__accepted_load + self.__rejected_load
        self.__optimal_load = min(total_resources, total_load)
        return ([len(self.__accepted_jobs), len(self.__rejected_jobs),
                 self.__accepted_load, self.__rejected_load, self.__optimal_load, self.__execution_time])

    # method to sort jobs in ascending order of their release times
    def _sort_jobs_ascending_release_time(self):
        self.__jobs.sort(key=lambda j: j.get_release_time())

    # method to sort machines so that most loaded stays on top and least loaded at the bottom
    def _sort_machines_descending_avail_time(self):
        self.__machines.sort(key=lambda m: m.get_available_time(), reverse=True)

    # method to return start time of a particular job on a particular machine
    def _get_start_time(self, job, core):
        release_time = job.get_release_time()
        machine_avail_time = self.__machines[core].get_available_time()

        start_time = max(machine_avail_time, release_time)
        return start_time

    # this method returns machine available time
    def _get_machine_avail_time(self, core):
        machine_avail_time = self.__machines[core].get_available_time()
        return machine_avail_time

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

    # method to update

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
        # start time point reference
        simulation_start_time = time.time()
        # sort all jobs in ascending order
        super()._sort_jobs_ascending_release_time()
        # for every job in the list, do
        while len(super().get_job_list()) > 0:
            # get the first job in the list
            job = super().get_job_fifo()
            # sort machines based on reverse order of remaining load
            super()._sort_machines_descending_avail_time()
            # check whether the job has enough cores to complete
            # considering multi-core jobs, last core for job c = m - job_core
            legal_completion_status = self.__check_legal_completion(job)
            if not legal_completion_status:
                continue
            # check whether the job can be legally completed before due time on available cores
            # greedy acceptance policy
            acceptance_status = self.__check_acceptance_status(job)
            if not acceptance_status:
                continue
            # allocate job based on greedy balanced allocation policy
            self.__allocate_greedy_balanced(job)
        # end time point reference
        simulation_end_time = time.time()
        execution_time = round(simulation_end_time - simulation_start_time, 4)
        super().update_execution_time(execution_time)
        # updating the run time logs
        super()._update_logs()
        # returning the result of the simulation
        return super()._results()

    def __check_legal_completion(self, job):
        # if a job has more cores than the one available in the simulation set-up, it can never be processed
        # hence the job is rejected
        start_core = super().get_machine_num() - job.get_job_core()
        if start_core < 0:
            super().update_rejected(job)
            return False
        else:
            return True

    def __check_acceptance_status(self, job):
        # if a job with 'c' cores can be completed on/before its due time on 'c' least loaded cores,
        # then it can be accepted. else, it is rejected
        start_core = super().get_machine_num() - job.get_job_core()
        completion_time = super()._get_completion_time(job, start_core)
        if completion_time <= job.get_due_time():
            return True
        else:
            super().update_rejected(job)
            return False

    def __allocate_greedy_balanced(self, job):
        # getting starting core of the job
        start_core = super().get_machine_num() - job.get_job_core()
        # allocate job to machine using super method
        super().allocate_job_to_core(job, start_core)

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
        # start time point reference
        simulation_start_time = time.time()
        # sort all jobs in ascending order
        super()._sort_jobs_ascending_release_time()
        # for every job in the list, do
        while len(super().get_job_list()) > 0:
            # get the first job in the list
            job = super().get_job_fifo()
            # sort machines based on reverse order of remaining load
            super()._sort_machines_descending_avail_time()
            # check whether the job has enough cores to complete
            # considering multi-core jobs, last core for job c = m - job_core
            legal_completion_status = self.__check_legal_completion(job)
            if not legal_completion_status:
                continue
            # check whether the job can be legally completed before due time on available cores
            # greedy acceptance policy
            acceptance_status = self.__check_acceptance_status(job)
            if not acceptance_status:
                continue
            # allocate job based on greedy balanced allocation policy
            self.__allocate_greedy_bestfit(job)
        # end time point reference
        simulation_end_time = time.time()
        execution_time = round(simulation_end_time - simulation_start_time, 4)
        super().update_execution_time(execution_time)
        # updating the run time logs
        super()._update_logs()
        # returning the result of the simulation
        return super()._results()

    def __check_legal_completion(self, job):
        # if a job has more cores than the one available in the simulation set-up, it can never be processed
        # hence the job is rejected
        start_core = super().get_machine_num() - job.get_job_core()
        if start_core < 0:
            super().update_rejected(job)
            return False
        else:
            return True

    def __check_acceptance_status(self, job):
        # if a job with 'c' cores can be completed on/before its due time on 'c' least loaded cores,
        # then it can be accepted. else, it is rejected
        start_core = super().get_machine_num() - job.get_job_core()
        completion_time = super()._get_completion_time(job, start_core)
        if completion_time <= job.get_due_time():
            return True
        else:
            super().update_rejected(job)
            return False

    def __allocate_greedy_bestfit(self, job):
        # getting starting core of the job
        start_core = super()._search_loaded_machine(job)
        # allocate job to machine using super method
        super().allocate_job_to_core(job, start_core)


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
        # start time point reference
        simulation_start_time = time.time()
        # sort all jobs in ascending order
        super()._sort_jobs_ascending_release_time()
        # calculate f values for the machine system
        f_values = self.__calculate_f_values_epsilon()
        # for every job in the list, do
        while len(super().get_job_list()) > 0:
            # get the first job in the list
            job = super().get_job_fifo()
            # sort machines based on reverse order of remaining load
            super()._sort_machines_descending_avail_time()
            # check whether the job has enough cores to complete
            # considering multi-core jobs, last core for job c = m - job_core
            legal_completion_status = self.__check_legal_completion(job)
            if not legal_completion_status:
                continue
            # check whether the job can be legally completed before due time on available cores
            # greedy acceptance policy
            deadline_threshold_acceptance_status = self.__check_deadline_threshold_acceptance_status(f_values, job)
            if not deadline_threshold_acceptance_status:
                continue
            # check whether the job can be legally completed before due time on available cores
            # greedy acceptance policy
            acceptance_status = self.__check_acceptance_status(job)
            if not acceptance_status:
                continue
            # allocate job based on greedy balanced allocation policy
            self.__allocate_greedy_bestfit(job)
        # end time point reference
        simulation_end_time = time.time()
        execution_time = round(simulation_end_time - simulation_start_time, 4)
        super().update_execution_time(execution_time)
        # updating the run time logs
        super()._update_logs()
        # returning the result of the simulation
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
        # super()._sort_machines_descending_avail_time()
        # Calculate deadline threshold of individual machines
        deadline_threshold_m = []
        for m in range(0, super().get_machine_num()):
            load_m = super().get_machine_list()[m].get_available_time() - release_time
            deadline_threshold_m.append(release_time + load_m * f_values[m + 1])
        # Return the maximum value
        return max(deadline_threshold_m)

    def __check_legal_completion(self, job):
        # if a job has more cores than the one available in the simulation set-up, it can never be processed
        # hence the job is rejected
        start_core = super().get_machine_num() - job.get_job_core()
        if start_core < 0:
            super().update_rejected(job)
            return False
        else:
            return True

    def __check_deadline_threshold_acceptance_status(self, f_values, job):
        # if due time is less than deadline threshold, reject the job
        # else, accept the job
        deadline_threshold = self.__calculate_deadline_threshold(f_values, job)
        if job.get_due_time() < deadline_threshold:
            super().update_rejected(job)
            return False
        else:
            return True

    def __check_acceptance_status(self, job):
        # if a job with 'c' cores can be completed on/before its due time on 'c' least loaded cores,
        # then it can be accepted. else, it is rejected
        start_core = super().get_machine_num() - job.get_job_core()
        completion_time = super()._get_completion_time(job, start_core)
        if completion_time <= job.get_due_time():
            return True
        else:
            super().update_rejected(job)
            return False

    def __allocate_greedy_bestfit(self, job):
        # getting starting core of the job
        start_core = super()._search_loaded_machine(job)
        # allocate job to machine using super method
        super().allocate_job_to_core(job, start_core)


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
        # start time point reference
        simulation_start_time = time.time()
        # sort all jobs in ascending order
        super()._sort_jobs_ascending_release_time()
        # for every job in the list, do
        while len(super().get_job_list()) > 0:
            # get the first job in the list
            job = super().get_job_fifo()
            # sort machines based on reverse order of remaining load
            super()._sort_machines_descending_avail_time()
            # check whether the job has enough cores to complete
            # considering multi-core jobs, last core for job c = m - job_core
            legal_completion_status = self.__check_legal_completion(job)
            if not legal_completion_status:
                continue
            # check whether the job can be legally completed before due time on available cores
            # greedy acceptance policy
            acceptance_status = self.__check_acceptance_status(job)
            if not acceptance_status:
                continue
            # allocate job based on greedy balanced allocation policy
            self.__allocate_greedy_minidle(job)
        # end time point reference
        simulation_end_time = time.time()
        execution_time = round(simulation_end_time - simulation_start_time, 4)
        super().update_execution_time(execution_time)
        # updating the run time logs
        super()._update_logs()
        # returning the result of the simulation
        return super()._results()

    def __check_legal_completion(self, job):
        # if a job has more cores than the one available in the simulation set-up, it can never be processed
        # hence the job is rejected
        start_core = super().get_machine_num() - job.get_job_core()
        if start_core < 0:
            super().update_rejected(job)
            return False
        else:
            return True

    def __check_acceptance_status(self, job):
        # if a job with 'c' cores can be completed on/before its due time on 'c' least loaded cores,
        # then it can be accepted. else, it is rejected
        start_core = super().get_machine_num() - job.get_job_core()
        completion_time = super()._get_completion_time(job, start_core)
        if completion_time <= job.get_due_time():
            return True
        else:
            super().update_rejected(job)
            return False

    def __allocate_greedy_minidle(self, job):
        # getting starting core of the job
        last_core = super().get_machine_num() - job.get_job_core()
        # reference variables for min idle execution
        minimum_idle_time = None
        minimum_idle_core = None
        # we move from the least loaded core to most loaded core
        for start_core in range(last_core, -1, -1):
            # completion time on this core
            completion_time = super()._get_completion_time(job, start_core)
            # when it is no longer possible to execute a job on given core, we stop
            if completion_time > job.get_due_time():
                break
            else:
                # calculate start time on this core
                start_time = super()._get_start_time(job, start_core)
                # variable to calculate idle time
                total_idle_time = 0
                # go through all the cores
                for core in range(start_core, start_core + job.get_job_core()):
                    # update idle time
                    total_idle_time += start_time - super().get_machine_list()[core].get_available_time()

                # for the first machine, update the min idle variables as such
                if minimum_idle_core is None:
                    minimum_idle_time = total_idle_time
                    minimum_idle_core = start_core

                # for remaining executions, update only when a new min setting is found
                # if there are multiple min settings, we use the machine which is most loaded
                if minimum_idle_time >= total_idle_time:
                    minimum_idle_time = total_idle_time
                    minimum_idle_core = start_core
        # once we have our min idle core, we schedule jobs on min idle to min idle + c cores
        # allocate job to machine using super method
        super().allocate_job_to_core(job, minimum_idle_core)


class AlgorithmGBalancedBF(Algorithm):
    """
        this class basically inherits all properties of the Algorithm class.
        first step is to check whether job can be processed completely with the available holes
        if so, we so ahead and schedule the job in the holes, without affecting the completion times on machines
        if not, then the traditional greedy balanced algorithm is followed.
    """

    def __init__(self, jobs, machines):
        super().__init__('greedybalancedbackfill', jobs, machines)

    def execute(self, trial=False):
        # start time point reference
        simulation_start_time = time.time()
        # sort all jobs in ascending order
        super()._sort_jobs_ascending_release_time()
        # for every job in the list, do
        while len(super().get_job_list()) > 0:
            # get the first job in the list
            job = super().get_job_fifo()
            # check backfill possibility
            backfill_status = super().check_and_allocate_backfill(job)
            if backfill_status:
                continue
            # sort machines based on reverse order of remaining load
            super()._sort_machines_descending_avail_time()
            # check whether the job has enough cores to complete
            # considering multi-core jobs, last core for job c = m - job_core
            legal_completion_status = self.__check_legal_completion(job)
            if not legal_completion_status:
                continue
            # check whether the job can be legally completed before due time on available cores
            # greedy acceptance policy
            acceptance_status = self.__check_acceptance_status(job)
            if not acceptance_status:
                continue
            # allocate job based on greedy balanced allocation policy
            self.__allocate_greedy_balanced(job)
        # end time point reference
        simulation_end_time = time.time()
        execution_time = round(simulation_end_time - simulation_start_time, 4)
        super().update_execution_time(execution_time)
        # updating the run time logs
        super()._update_logs()
        # returning the result of the simulation
        return super()._results()

    def __check_legal_completion(self, job):
        # if a job has more cores than the one available in the simulation set-up, it can never be processed
        # hence the job is rejected
        start_core = super().get_machine_num() - job.get_job_core()
        if start_core < 0:
            super().update_rejected(job)
            return False
        else:
            return True

    def __check_acceptance_status(self, job):
        # if a job with 'c' cores can be completed on/before its due time on 'c' least loaded cores,
        # then it can be accepted. else, it is rejected
        start_core = super().get_machine_num() - job.get_job_core()
        completion_time = super()._get_completion_time(job, start_core)
        if completion_time <= job.get_due_time():
            return True
        else:
            super().update_rejected(job)
            return False

    def __allocate_greedy_balanced(self, job):
        # getting starting core of the job
        start_core = super().get_machine_num() - job.get_job_core()
        # allocate job to machine using super method
        super().allocate_job_to_core(job, start_core)


class AlgorithmGBestFitBF(Algorithm):
    """
        this class basically inherits all properties of the Algorithm class.
        first step is to check whether job can be processed completely with the available holes
        if so, we so ahead and schedule the job in the holes, without affecting the completion times on machines
        if not, then the traditional greedy bestfit algorithm is followed.
    """

    def __init__(self, jobs, machines):
        super().__init__('greedybestfitbackfill', jobs, machines)

    def execute(self, trial=False):
        # start time point reference
        simulation_start_time = time.time()
        # sort all jobs in ascending order
        super()._sort_jobs_ascending_release_time()
        # for every job in the list, do
        while len(super().get_job_list()) > 0:
            # get the first job in the list
            job = super().get_job_fifo()
            # check backfill possibility
            backfill_status = super().check_and_allocate_backfill(job)
            if backfill_status:
                continue
            # sort machines based on reverse order of remaining load
            super()._sort_machines_descending_avail_time()
            # check whether the job has enough cores to complete
            # considering multi-core jobs, last core for job c = m - job_core
            legal_completion_status = self.__check_legal_completion(job)
            if not legal_completion_status:
                continue
            # check whether the job can be legally completed before due time on available cores
            # greedy acceptance policy
            acceptance_status = self.__check_acceptance_status(job)
            if not acceptance_status:
                continue
            # allocate job based on greedy balanced allocation policy
            self.__allocate_greedy_bestfit(job)
        # end time point reference
        simulation_end_time = time.time()
        execution_time = round(simulation_end_time - simulation_start_time, 4)
        super().update_execution_time(execution_time)
        # updating the run time logs
        super()._update_logs()
        # returning the result of the simulation
        return super()._results()

    def __check_legal_completion(self, job):
        # if a job has more cores than the one available in the simulation set-up, it can never be processed
        # hence the job is rejected
        start_core = super().get_machine_num() - job.get_job_core()
        if start_core < 0:
            super().update_rejected(job)
            return False
        else:
            return True

    def __check_acceptance_status(self, job):
        # if a job with 'c' cores can be completed on/before its due time on 'c' least loaded cores,
        # then it can be accepted. else, it is rejected
        start_core = super().get_machine_num() - job.get_job_core()
        completion_time = super()._get_completion_time(job, start_core)
        if completion_time <= job.get_due_time():
            return True
        else:
            super().update_rejected(job)
            return False

    def __allocate_greedy_bestfit(self, job):
        # getting starting core of the job
        start_core = super()._search_loaded_machine(job)
        # allocate job to machine using super method
        super().allocate_job_to_core(job, start_core)


class AlgorithmOSScheduling(Algorithm):

    def __init__(self, jobs, machines, epsilon):
        super().__init__("onlineslackscheduling", jobs, machines)
        self.__reference_time = 0
        self.__epsilon = epsilon
        self.__working_list = []

    def execute(self):
        # start time point reference
        simulation_start_time = time.time()
        # sort all jobs in ascending order
        super()._sort_jobs_ascending_release_time()
        # calculate function value
        value_fme = self.__function_m_eps()
        # for every job in the list, do
        job_count = 0
        while len(super().get_job_list()) > 0:
            # get the first job in the list
            job = super().get_job_fifo()
            job.print_details() # DELETE
            # useful job properties
            job_due_time = job.get_due_time()
            job_processing_time = job.get_processing_time()
            # set reference time to be the release time of the job
            self.__reference_time = job.get_release_time()
            # update working list
            self.__update_working_list(job_processing_time, job_due_time)
            # tentatively accept the job and create a new accepted list
            tentative_accepted_list = self.__working_list + [job]

            # DELETE
            print("Working list has {} jobs".format(len(self.__working_list)))
            """
            print("Details of the working list : ")
            print([j.get_job_id() for j in self.__working_list])
            
            job_count += 1
            if job_count > 1000:
                break
            """
            # DELETE
            rejection_status = False
            for job_i in tentative_accepted_list:
                # job properties which are used in calculations
                job_i_processing_time = job_i.get_processing_time()
                job_i_due_time = job_i.get_due_time()
                # expressions which define the check conditions
                expression_1 = job_i_processing_time > (job_due_time - self.__reference_time) / (1 + self.__epsilon)
                expression_2 = (job_due_time - self.__reference_time) / (1 + self.__epsilon) \
                                                                             + self.__reference_time >= job_due_time
                expression_3 = job_i_due_time >= job_due_time
                expression_4 = job_i_due_time > job_due_time - job_processing_time
                expression_5 = job_i_due_time < job_due_time
                # if none of the check conditions matter, we can simply move on to next job
                if not (expression_1 and expression_2):
                    if not expression_3:
                        if not (expression_4 and expression_5):
                            continue

                v_accept_ref = 0
                v_accept_due = 0
                v_min = 0
                for job_j in tentative_accepted_list:
                    time_expression = (job_due_time - self.__reference_time) / (1 + self.__epsilon)
                    v_accept_ref += self.__calculate_v_accept_job(job_j, time_expression)
                    v_accept_due += self.__calculate_v_accept_job(job_j, job_i_due_time)
                    v_min += self.__calculate_v_min_job(job_j, job_i_due_time)

                expression_6 = v_accept_ref > \
                               value_fme * (job_i_due_time - self.__reference_time) / (1 + self.__epsilon)
                expression_7 = v_accept_due > value_fme * (job_i_due_time - self.__reference_time)
                expression_8 = v_min > super().get_machine_num() * (job_i_due_time - self.__reference_time)

                if expression_1 and expression_2:
                    if expression_6:
                        super().update_rejected(job)
                        rejection_status = True
                        break

                if expression_3:
                    if expression_7:
                        super().update_rejected(job)
                        rejection_status = True
                        break

                if expression_4 and expression_5:
                    if expression_8:
                        super().update_rejected(job)
                        rejection_status = True
                        break

            if not rejection_status:
                super().update_accepted(copy.deepcopy(job))
                self.__working_list.append(copy.deepcopy(job))
        # end time point reference
        simulation_end_time = time.time()
        execution_time = round(simulation_end_time - simulation_start_time, 4)
        super().update_execution_time(execution_time)
        # updating the run time logs
        super()._update_logs()
        # returning the result of the simulation
        return super()._results()

    def __update_working_list(self, processing_time, due_time):
        # self.__working_list = copy.deepcopy(super().get_accepted_jobs())
        due_dates = np.array([j.get_due_time() for j in self.__working_list])
        index_array = np.where(due_dates < self.__reference_time)
        indices = index_array[0].tolist()
        while len(indices) > 0:
            index = indices.pop(-1)
            self.__working_list.pop(index)

    def __function_m_eps(self):
        expression_1 = ((1 + self.__epsilon) / self.__epsilon) ** (1 / super().get_machine_num())
        expression_2 = (1 + self.__epsilon)
        expression_3 = expression_1 - 1
        value = (1 / expression_2) * (expression_1 / expression_3)
        return value

    def __calculate_v_min_job(self, job, reference_time):
        if job.get_due_time() - job.get_processing_time() >= reference_time:
            return 0
        elif job.get_due_time() <= reference_time:
            return job.get_processing_time()
        else:
            return job.get_processing_time() - job.get_due_time() + reference_time

    def __calculate_v_accept_job(self, job, reference_time):
        expression = job.get_due_time() - (job.get_due_time() / (1 + self.__epsilon))
        if job.get_due_time() <= reference_time:
            return job.get_processing_time()
        elif job.get_due_time() > reference_time > expression:
            return max(0, job.get_processing_time() - (job.get_due_time() / (1 + self.__epsilon)))
        elif expression >= reference_time > job.get_due_time() - job.get_processing_time():
            return job.get_processing_time() - job.get_due_time() + reference_time
        elif job.get_due_time() - job.get_processing_time() >= reference_time:
            return 0

