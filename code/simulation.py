from functions import Operations
from algorithms import AlgorithmGBalanced
from settings import SETS, SLACKS, SD


class Simulation:

    def __init__(self):
        self.__operations = Operations()

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





