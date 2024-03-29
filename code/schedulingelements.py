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

        self.__weight = 0
        self.__start_time = 0
        self.__completion_time = 0

    def update(self, start_time, completion_time, weight=0):
        self.__start_time = start_time
        self.__completion_time = completion_time
        self.__weight = weight

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

    def get_weight(self):
        return self.__weight

    def get_details(self):
        return ("{} with {} cores: p_j = {}, r_j = {}, "
                "d_j = {}, start = {}, end = {}, weight = {}".format(self.__job_id,
                                                                     self.__job_core,
                                                                     self.__processing_time,
                                                                     self.__release_time,
                                                                     self.__due_time,
                                                                     self.__start_time,
                                                                     self.__completion_time,
                                                                     self.__weight))

    def get_stat(self):
        return ("{}; {}; {}; {}; {}; {}; {}; {};".format(self.__job_id,
                                                         self.__job_core,
                                                         self.__processing_time,
                                                         self.__release_time,
                                                         self.__due_time,
                                                         self.__start_time,
                                                         self.__completion_time,
                                                         self.__weight))

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

    def __init__(self, container_id):
        self.__id = container_id
        self.__job = None
        self.__start_time = None
        self.__end_time = None
        self.__vacant_size = None
        self.__machine = None
        self.__type = None

    def assign(self, job, start_time, end_time, machine_id, container_type=0):
        self.__job = job
        self.__start_time = start_time
        self.__end_time = end_time
        self.__machine = machine_id
        self.__vacant_size = 0
        self.__type = container_type

    def reserve(self, start_time, end_time, vacant_size, machine_id):
        self.__start_time = start_time
        self.__end_time = end_time
        self.__vacant_size = vacant_size
        self.__machine = machine_id

    def update(self, start_time, end_time, container_type):
        self.__start_time = start_time
        self.__end_time = end_time
        self.__type = container_type

    def get_id(self):
        return self.__id

    def get_job(self):
        return self.__job

    def get_start_time(self):
        return self.__start_time

    def get_end_time(self):
        return self.__end_time

    def get_machine(self):
        return self.__machine

    def get_vacant_size(self):
        return self.__vacant_size

    def get_type(self):
        return self.__type

    def get_details(self):
        if self.__vacant_size > 0:
            return ("Vacant Container {}: Size {}, start = {}, end = {}".format(self.__id,
                                                                                self.__vacant_size,
                                                                                self.__start_time,
                                                                                self.__end_time))
        else:
            return ("Container {}: Job {}, start = {}, end = {} on machine {}".format(self.__id,
                                                                                      self.__job.get_job_id(),
                                                                                      self.__start_time,
                                                                                      self.__end_time,
                                                                                      self.__machine))

    def print_details(self):
        print(self.get_details())


class Machine:
    """
    Each machine class represents a single core in the real world.
    An object of this class holds a series of containers, which in turn hold jobs processed on this core.
    Once a container is deployed on the machine, the available time of the machine is updated accordingly.

    There are additional methods to access the schedule as a string of job ids as well as to print these details.
    """

    def __init__(self, machine_id):
        self.__machine_id = machine_id
        self.__schedule = []
        self.__available_time = 0

    def update(self, container, completion_time):
        self.__schedule.append(container)
        self.sort_containers_ascending_start_time()
        self.__available_time = completion_time

    def attach(self, container):
        self.__schedule.append(container)

    def get_machine_id(self):
        return self.__machine_id

    def get_available_time(self):
        return self.__available_time

    def get_scheduled_containers(self):
        return self.__schedule

    def get_container_index(self, reference_time):
        c_start = 0
        c_end = len(self.__schedule) - 1
        while True:
            c_mid = int((c_start + c_end) / 2)
            if c_mid == c_start == c_end:
                if self.__schedule[-1].get_end_time() <= reference_time:
                    return None
                else:
                    return c_mid

            start_time = self.__schedule[c_mid].get_start_time()
            end_time = self.__schedule[c_mid].get_end_time()
            if start_time > reference_time:
                c_end = c_mid - 1
            if end_time <= reference_time:
                c_start = c_mid + 1
            if start_time == reference_time or start_time <= reference_time < end_time:
                return c_mid

    def sort_containers_ascending_start_time(self):
        if len(self.__schedule) > 0:
            self.__schedule.sort(key=lambda c: c.get_start_time(), reverse=False)

    def get_schedule(self):
        schedule = 'Machine ' + str(self.__machine_id) + ':'
        self.__schedule.sort(key=lambda c: c.get_end_time())
        for container in self.__schedule:
            if container.get_job() is not None:
                schedule += container.get_job().get_job_id() + ' '
        return schedule

    def print_schedule(self):
        print(self.get_schedule())

