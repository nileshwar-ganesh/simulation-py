class Job:
    """
    Each submitted job is stored as an object of the Job class.
    The basic properties of each job are id, processing time, release time, due time and job cores.
    These parameters do not change with time and are fixed at the time of submission.
    There are methods only to read these parameters, to prevent modification by accident.

    The start time and completion times of the jobs depend on the way they are scheduled.
    There are both read and write methods to access these parameters.
    There are additional methods to access job details as a string as well as to print these details.
    """
    def __init__(self, job_id, processing_time, release_time, due_time, job_core):
        self.__job_id = job_id
        self.__processing_time = processing_time
        self.__release_time = release_time
        self.__due_time = due_time
        self.__job_core = job_core

        self.__start_time = 0
        self.__completion_time = 0

    def update(self, start_time, completion_time):
        self.__start_time = start_time
        self.__completion_time = completion_time

    def get_job_id(self):
        return self.__job_id

    def get_processing_time(self):
        return self.__processing_time

    def get_release_time(self):
        return self.__release_time

    def get_due_time(self):
        return self.__due_time

    def get_job_core(self):
        return self.__job_core

    def get_details(self):
        return ("{} with {} cores: p_j = {}, r_j = {}, d_j = {}, start = {}, end = {}".format(self.__job_id,
                                                                                              self.__job_core,
                                                                                              self.__processing_time,
                                                                                              self.__release_time,
                                                                                              self.__due_time,
                                                                                              self.__start_time,
                                                                                              self.__completion_time))

    def print_details(self):
        print(self.get_details())


class Container:
    """
    Container class becomes building block for schedule on a machine.
    Each container object will have a unique id, a job, start times and end times.
    In case of non-preemptive schedule, each job will have one container.
    In case of preemptive schedule, a job may be distributed across 2 or more containers.

    There are additional methods to access container details as a string as well as to print these details.
    """

    def __init__(self, container_id, job, start_time, end_time):
        self.__id = container_id
        self.__job = job
        self.__start_time = start_time
        self.__end_time = end_time

    def update(self, start_time, end_time):
        self.__start_time = start_time
        self.__end_time = end_time

    def get_id(self):
        return self.__id

    def get_job(self):
        return self.__job

    def get_start_time(self):
        return self.__start_time

    def get_end_time(self):
        return self.__end_time

    def get_details(self):
        return ("Container {}: Job {}, start = {}, end = {}".format(self.__id,
                                                                  self.__job.get_job_id(),
                                                                  self.__start_time,
                                                                  self.__end_time))

    def print_details(self):
        print(self.get_details())


class Machine:
    """
    Each machine class represents a single core in the real world.
    An object of this class holds a series of containers, which in turn hold jobs processed on this core.
    Once a container is deployed on the machine, the available time of the machine is updated accordingly.

    There are additional methods to access the schedule as a string of job ids as well as to print these details.
    """

    def __init__(self):
        self.__schedule = []
        self.__available_time = 0

    def update(self, container, completion_time):
        self.__schedule.append(container)
        self.__available_time = completion_time

    def get_available_time(self):
        return self.__available_time

    def get_schedule(self):
        schedule = ''
        for container in self.__schedule:
            schedule += container.get_job().get_job_id() + " "
        return schedule

    def print_schedule(self):
        print(self.get_schedule())
