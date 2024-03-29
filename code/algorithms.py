import copy
import sys
import time
import math
import numpy as np
import copy as cp
from code.functions import Operations
from code.schedulingelements import Container


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

    def read_job_fifo(self):
        return self.__jobs[0]

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

    def get_container_id(self):
        id = self.__container_id
        self.__container_id += 1
        return id

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

    # this method returns machine reference time
    def _get_machine_reference_time(self, core):
        machine_reference_time = self.__machines[core].get_reference_time()
        return machine_reference_time

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
        super().__init__('slack', jobs, machines)
        self.__epsilon = epsilon
        self.__array_length = 450000  # release date + 2 * processing time (86400)
        self.__v_start = np.zeros(self.__array_length)
        self.__v_end = np.zeros(self.__array_length)
        self.__tau_values = [0]
        self.__d_min = 0
        self.__fp_epsilon_m = None

    def execute(self):
        # start time point reference
        simulation_start_time = time.time()
        # sort all jobs in ascending order
        super()._sort_jobs_ascending_release_time()
        # calculate threshold value
        self.__calculate_threshold_expression()
        # for every job in the list, do
        while len(super().get_job_list()) > 0:
            job = super().get_job_fifo()
            self.__run_acceptance_check(job)

        # end time point reference
        simulation_end_time = time.time()
        execution_time = round(simulation_end_time - simulation_start_time, 4)
        super().update_execution_time(execution_time)
        # updating the run time logs
        super()._update_logs()
        # returning the result of the simulation
        return super()._results()

    def __calculate_threshold_expression(self):
        # this works, verified with recursive equation
        cp_epsilon_1 = (1 + self.__epsilon) / self.__epsilon
        expression_1 = 1 + self.__epsilon
        expression_2 = cp_epsilon_1 ** (1 / super().get_machine_num()) - 1
        expression = expression_1 * expression_2
        self.__fp_epsilon_m = 1 / expression

    def __calculate_v_start_array(self, job):
        limit_2 = job.get_release_time()
        limit_3 = job.get_release_time() + job.get_processing_time()

        array_1 = np.zeros(limit_2 + 1)
        array_2 = np.array([i for i in range(1, limit_3 - limit_2)])
        array_3 = np.ones(self.__array_length - limit_3) * job.get_processing_time()
        self.__v_start_job = np.hstack((array_1, array_2, array_3))
        self.__v_start += self.__v_start_job

    def __calculate_v_end_array(self, job):
        limit_2 = job.get_due_time() - job.get_processing_time()
        limit_3 = job.get_due_time()

        array_1 = np.zeros(limit_2 + 1)
        array_2 = np.array([i for i in range(1, limit_3 - limit_2)])
        array_3 = np.ones(self.__array_length - limit_3) * job.get_processing_time()
        self.__v_end_job = np.hstack((array_1, array_2, array_3))
        self.__v_end += self.__v_end_job

    def __update_v_values(self, job):
        self.__calculate_v_start_array(job)
        self.__calculate_v_end_array(job)

    def __calculate_v_min(self, t, t_prime):
        return max(0, self.__v_end[t_prime] - self.__v_start[t])

    def __update_d_min(self, job, compensation_load):
        job_release_time = job.get_release_time()
        # the maximum known so far remains at the last due date known
        max_load_val = max(self.__v_end[self.__tau_values[-1]] - self.__v_end[job_release_time], 0)
        total_load = compensation_load + max_load_val
        self.__d_min = job_release_time + (total_load / self.__fp_epsilon_m)

    def __run_acceptance_check(self, job):
        job_release_time = job.get_release_time()
        job_due_time = job.get_due_time()
        self.__d_min = max(self.__d_min, job_release_time)
        expression_1 = (self.__d_min - job_release_time) * self.__fp_epsilon_m
        if self.__d_min > self.__tau_values[-1]:
            _d_min = self.__tau_values[-1]
        else:
            _d_min = round(self.__d_min)
        expression_2 = self.__v_end[_d_min] - self.__v_end[job_release_time]
        compensation_load = max(0, expression_1 - expression_2)
        if job_due_time >= self.__d_min:
            super().update_accepted(job)
            self.__tau_values.append(job_due_time)
            self.__update_v_values(job)
            self.__update_d_min(job, compensation_load)
        else:
            super().update_rejected(job)


class AlgorithmRegion(Algorithm):

    def __init__(self, jobs, machines, epsilon, alpha=1):
        super().__init__('region', jobs, machines)
        # system parameters - no commitment model
        self.__alpha = alpha
        self.__beta = epsilon / 4
        self.__delta = epsilon / 2

        self.__available_jobs = []
        self.__released_jobs = []
        self.__reference_time = None

    def execute(self):
        # start time point reference
        simulation_start_time = time.time()
        # sort all jobs in ascending order
        super()._sort_jobs_ascending_release_time()
        # additional time points
        current_release_time = 0
        incoming_time = 0
        while len(super().get_job_list()) > 0:
            # get the first job in the list
            job = super().read_job_fifo()
            self.__reference_time = job.get_release_time()

            # collect all jobs released at the same time
            while super().read_job_fifo().get_release_time() == self.__reference_time:
                self.__released_jobs.append(super().get_job_fifo())
                # if there are no jobs left in the list, then break
                if len(super().get_job_list()) <= 0:
                    break

            # check for the next incoming job
            if len(super().get_job_list()) > 0:
                # there are still jobs left
                incoming_time = super().read_job_fifo().get_release_time()
            else:
                # assign some large value
                incoming_time = sys.maxsize

            # check for preemption
            # status is 1, if new jobs are released that overlap with machine time
            # status is 2, if there are no more small jobs left for preemption
            status = self.__preemption_routine()

            #if status:
            #    continue
            #else:
            # all released jobs till now are available
            self.__available_jobs += copy.deepcopy(self.__released_jobs)
            self.__released_jobs = []
            # jobs need to be scheduled in SPT order
            self.__available_jobs.sort(key=lambda j: j.get_processing_time(), reverse=False)
            while len(self.__available_jobs) > 0:
                # if there exists at least one machine, which has processing power before next incoming job
                # schedule from available jobs
                super()._sort_machines_descending_avail_time()
                earliest_available_time = super().get_machine_list()[-1].get_available_time()
                # if there are additional jobs which are released in between, then we need to consider then first
                if earliest_available_time >= incoming_time:
                    break
                job = self.__available_jobs.pop(0)
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

    def __preemption_routine(self):
        # sort all newly released jobs based on the processing time
        self.__released_jobs.sort(key=lambda j: j.get_processing_time(), reverse=False)
        # check for preemption for newly released jobs
        while len(self.__released_jobs) > 0:
            job = self.__released_jobs[0]
            # job properties
            job_processing_time = job.get_processing_time()
            job_release_time = job.get_release_time()
            job_due_time = job.get_due_time()
            # sort machines based on reference time - smallest to largest
            super()._sort_machines_descending_avail_time()
            status_assigned = False
            for m in range(0, super().get_machine_num()):
                # if machine does not have even a single container, no need of preemption
                # exit preemption routine for this machine and check other machines
                if len(super().get_machine_list()[m].get_scheduled_containers()) <= 0:
                    continue
                container_index = super().get_machine_list()[m].get_container_index(self.__reference_time)
                # if there are no suitable containers, that means the job can be scheduled at the end
                # exit preemption routine for this machine and check other machines
                if container_index is None:
                    continue
                total_containers = len(super().get_machine_list()[m].get_scheduled_containers())
                # find all containers that overlap with the time period
                # earliest start time possible = release date of the job
                # latest start time possible = due date of the job - processing time of the job (tight)
                container_indices = []
                for c in range(container_index, total_containers):
                    start_time = self.get_machine_list()[m].get_scheduled_containers()[c].get_start_time()
                    if start_time > job_due_time - job_processing_time:
                        break
                    else:
                        container_indices.append(c)

                # now there are no overlapping regions, simply continue to next machine
                if len(container_indices) <= 0:
                    continue
                else:
                    # check whether the region can be preempted
                    # conditions p_i < beta * p_j for all available containers on this machine
                    for index in container_indices:
                        start_time = self.get_machine_list()[m].get_scheduled_containers()[index] \
                            .get_start_time()
                        end_time = self.get_machine_list()[m].get_scheduled_containers()[index] \
                            .get_end_time()
                        processing_time_j = end_time - start_time
                        container_type = self.get_machine_list()[m].get_scheduled_containers()[index].get_type()
                        container_start_time = self.get_machine_list()[m].get_scheduled_containers()[index] \
                            .get_start_time()
                        # job cannot be preempted based on the processing time condition
                        if job_processing_time >= self.__beta * processing_time_j:
                            continue
                        else:
                            # if interval is starting interval, then start time and release time should not overlap
                            if container_type == 0 and job_release_time == container_start_time:
                                continue
                            else:
                                old_container_start = container_start_time
                                split_container_end_time = None
                                # assign the job
                                container_start_time = max(job_release_time, container_start_time)
                                container_size = self.__alpha * job_processing_time
                                container_end_time = container_start_time + container_size
                                machine_id = super().get_machine_list()[m].get_machine_id()
                                new_container = Container(super().get_container_id())
                                new_container.assign(job, container_start_time, container_end_time, machine_id, 0)

                                # check whether the previous interval needs to be split
                                split_container = None
                                if container_start_time == old_container_start:
                                    # no need for additional container
                                    # we can fit in new container and simply push the existing one to later time
                                    container_start_time = container_end_time
                                    container_end_time = super().get_machine_list()[m]. \
                                        get_scheduled_containers()[index].get_end_time() + container_size
                                    super().get_machine_list()[m].get_scheduled_containers()[index] \
                                        .update(container_start_time, container_end_time, 1)
                                else:
                                    # in case of a split, we need to get additional start time and end time for new
                                    # split container, which starts after the container of our new small job
                                    split_container_start_time = container_end_time
                                    split_container_end_time = super().get_machine_list()[m]. \
                                        get_scheduled_containers()[index].get_end_time() + container_size
                                    container_end_time = container_start_time
                                    container_start_time = super().get_machine_list()[m]. \
                                        get_scheduled_containers()[index].get_start_time()
                                    container_type = super().get_machine_list()[m]. \
                                        get_scheduled_containers()[index].get_type()
                                    super().get_machine_list()[m].get_scheduled_containers()[index] \
                                        .update(container_start_time, container_end_time, container_type)

                                    # creating a new split container
                                    split_job = super().get_machine_list()[m]. \
                                        get_scheduled_containers()[index].get_job()
                                    machine_id = super().get_machine_list()[m].get_machine_id()
                                    split_container = Container(super().get_container_id())
                                    split_container.assign(split_job, split_container_start_time,
                                                           split_container_end_time, machine_id, 1)

                                # update values for all following containers
                                for c in range(index + 1, total_containers):
                                    container_start_time = super().get_machine_list()[m].get_scheduled_containers()[c].\
                                        get_start_time() + container_size
                                    container_end_time = super().get_machine_list()[m].get_scheduled_containers()[c]. \
                                        get_end_time() + container_size
                                    container_type = super().get_machine_list()[m].get_scheduled_containers()[c]. \
                                        get_type()
                                    super().get_machine_list()[m].get_scheduled_containers()[c]. \
                                        update(container_start_time, container_end_time, container_type)

                                # add additional containers to the schedule (new, split)
                                available_time = super().get_machine_list()[m].get_scheduled_containers()[-1] \
                                    .get_end_time()
                                if split_container_end_time is not None:
                                    available_time = max(split_container_end_time, available_time)
                                super().get_machine_list()[m].update(new_container, available_time)
                                if split_container_end_time is not None:
                                    super().get_machine_list()[m].update(split_container, available_time)

                                status_assigned = True
                                break
                # if job is assigned, then we move on to the next job
                if status_assigned:
                    break
            # if job is assigned, then we move on to the next job
            if status_assigned:
                # here we update the new job into the schedule
                super().update_accepted(job)
                self.__released_jobs.pop(0)
            else:
                return False  # smallest job cannot be preempted, so go back to normal allocation
        return True  # if all jobs can be assigned via preemption, then return true

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