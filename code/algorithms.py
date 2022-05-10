import os
import sys
import time
import math
from functions import Operations
from settings import RESULT_FOLDER
from schedulingelements import Job, Container, Machine


class Algorithm:
    def __init__(self, algorithm_id, jobs, machines, trial=False):
        self.__jobs = jobs
        self.__machines = machines

        self.__id = algorithm_id
        self.__operations = Operations()
        self.__job_num = len(jobs)
        self.__machine_num = len(machines)
        self.__execution_time = None

        self.__containers = []
        self.__accepted_jobs = []
        self.__rejected_jobs = []
        self.__accepted_load = 0
        self.__rejected_load = 0
        self.__optimal_load = 0

        self.__trial_mode = trial

    def get_job_list(self):
        return self.__jobs

    def get_job_fifo(self):
        return self.__jobs.pop(0)

    def get_machine_list(self):
        return self.__machines

    def get_machine_num(self):
        return self.__machine_num

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

    def _results(self):
        self.__machines.sort(key=lambda m:m.get_available_time(), reverse=True)
        makespan = self.__machines[0].get_available_time()
        total_resources = len(self.__machines) * makespan
        total_load = self.__accepted_load + self.__rejected_load
        self.__optimal_load = min(total_resources, total_load)
        return ([len(self.__accepted_jobs), len(self.__rejected_jobs),
                 self.__accepted_load, self.__rejected_load, self.__optimal_load])

    def _sort_jobs_ascending_release_time(self):
        self.__jobs.sort(key=lambda j:j.get_release_time())

    def _sort_machines_descending_avail_time(self):
        self.__machines.sort(key=lambda m:m.get_available_time(), reverse=True)

    def _get_start_time(self, job, core):
        release_time = job.get_release_time()
        machine_avail_time = self.__machines[core].get_available_time()

        start_time = max(machine_avail_time, release_time)
        return start_time

    def _get_completion_time(self, job, core):
        release_time = job.get_release_time()
        processing_time = job.get_processing_time()
        machine_avail_time = self.__machines[core].get_available_time()

        completion_time = max(machine_avail_time, release_time) + processing_time
        return completion_time

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

    def _update_logs(self):
        if not self.__trial_mode:
            self.__operations.update_system_log(self.__id, self.__job_num, self.__machine_num, self.__execution_time)
            self.__operations.update_algorithm_log(self.__id, self.__job_num, self.__machine_num, self.__execution_time)
            self.__operations.update_machine_log(self.__id, self.__machines)
            self.__operations.update_job_log(self.__id, self.__accepted_jobs, self.__rejected_jobs)


class AlgorithmGBalanced(Algorithm):

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
            start_time = super()._get_start_time(job, start_core)
            completion_time = super()._get_completion_time(job, start_core)
            if completion_time <= job.get_due_time():
                for core in range(start_core, super().get_machine_num()):
                    container = Container(container_id)
                    container.assign(job, start_time, completion_time,
                                     super().get_machine_list()[core].get_machine_id())

                    self.update_machine(core, container, completion_time)
                    self.update_container_list(container)
                    container_id += 1

                job.update(start_time, completion_time)
                self.update_accepted(job)
            else:
                self.update_rejected(job)
        simulation_end_time = time.time()
        execution_time = round(simulation_end_time - simulation_start_time, 4)
        self.update_execution_time(execution_time)

        super()._update_logs()
        return super()._results()


class AlgorithmGBestFit(Algorithm):

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
            start_time = super()._get_start_time(job, start_core)
            completion_time = super()._get_completion_time(job, start_core)
            if completion_time <= job.get_due_time():
                start_core = super()._search_loaded_machine(job)

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

    def __init__(self, jobs, machines, epsilon):
        super().__init__('threshold', jobs, machines)
        self.__epsilon = epsilon

    def execute(self):
        pass

class AlgorithmGBalancedBF:

    def __init__(self):
        pass

class AlgorithmGBestFitBF:

    def __init__(self):
        pass
