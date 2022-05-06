import time
from functions import Operations
from schedulingelements import Job, Container, Machine


class AlgorithmGBalanced:

    def __init__(self, jobs, machines):
        self.__jobs = jobs
        self.__machines = machines

        self.__id = 'Greedy Balanced'
        self.operations = Operations()

    def execute(self):
        container_id = 0
        accepted_jobs = []
        rejected_jobs = []

        self.operations.update_system_log("Started {} with {} jobs and {} machines.".format(self.__id,
                                                                                            len(self.__jobs),
                                                                                            len(self.__machines)))
        simulation_start_time = time.time()
        while len(self.__jobs) > 0:
            job = self.__jobs.pop(0)

            # Sort machines based on reverse order of remaining load
            self.__machines.sort(key=lambda m:m.get_available_time(), reverse=True)

            # Check whether the job can be legally completed
            machine = self.__machines[-1]
            machine_avail_time = machine.get_available_time()
            release_time = job.get_release_time()
            due_time = job.get_due_time()
            processing_time = job.get_processing_time()
            start_time = max(machine_avail_time, release_time)
            completion_time = start_time + processing_time
            if completion_time < due_time:
                container = Container(container_id)
                container.assign(job, start_time, completion_time, machine.get_machine_id())
                self.__machines[-1].update(container, completion_time)
                container_id += 1
        simulation_end_time = time.time()
        simulation_time = round(simulation_end_time - simulation_start_time, 4)
        self.operations.update_system_log("Finished simulation in {} seconds.".format(simulation_time))

    def log(self):
        self.operations.update_algorithm_log(self.__id, )


class AlgorithmGBestFit:

    def __init__(self):
        pass

class AlgorithmThreshold:

    def __init__(self):
        pass

class AlgorithmGBalancedBF:

    def __init__(self):
        pass

class AlgorithmGBestFitBF:

    def __init__(self):
        pass
