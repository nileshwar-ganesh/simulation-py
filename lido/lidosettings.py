from code.settings import SLACKS, SD


class Lido:

    def __init__(self):
        pass

    @staticmethod
    def run_settings(file_name):
        data = file_name.strip().split('-')
        set_num = int(data[1])
        core = int(data[2])

        data = data[3].split('.')
        pool = int(data[0]) - 1

        return [set_num, core, pool]

    @staticmethod
    def parallelization_parameters(trace_id, core, slack_set, set_num,
                                   no_split, two_split, three_split, five_split, nine_split,
                                   sd_split_four, sd_split_two, sd_split_one):
        # parallelization run parameters
        parameters_no_split = []
        parameters_two_split = []
        parameters_three_split = []
        parameters_five_split = []
        parameters_nine_split = []
        parameters_sd_split_four = []
        parameters_sd_split_two = []
        parameters_sd_split_one = []

        # for all 31 days in 2019a/2019e, do
        for day in range(1, 32):
            # no split - no explicit need to define slack and sd range
            if day in no_split:
                parameters_no_split.append((day, trace_id, core, slack_set, set_num))

            # two split - slack range split between [0.1, 0.5] and [0.6, 0.9]
            if day in two_split:
                parameters_two_split.append((day, trace_id, core, slack_set, set_num, [i / 10 for i in range(1, 6)]))
                parameters_two_split.append((day, trace_id, core, slack_set, set_num, [i / 10 for i in range(6, 10)]))
            # three split - slack range split between [0.1, 0.3], [0.4, 0.6] and [0.7, 0.9]
            if day in three_split:
                parameters_three_split.append((day, trace_id, core, slack_set, set_num, [i / 10 for i in range(1, 4)]))
                parameters_three_split.append((day, trace_id, core, slack_set, set_num, [i / 10 for i in range(4, 7)]))
                parameters_three_split.append((day, trace_id, core, slack_set, set_num, [i / 10 for i in range(7, 10)]))
            # five split - slack range split between [0.1, 0.2], [0.3, 0.4], [0.5, 0.6], [0.7, 0.8] and [0.9]
            if day in five_split:
                parameters_five_split.append((day, trace_id, core, slack_set, set_num, [i / 10 for i in range(1, 3)]))
                parameters_five_split.append((day, trace_id, core, slack_set, set_num, [i / 10 for i in range(3, 5)]))
                parameters_five_split.append((day, trace_id, core, slack_set, set_num, [i / 10 for i in range(5, 7)]))
                parameters_five_split.append((day, trace_id, core, slack_set, set_num, [i / 10 for i in range(7, 9)]))
                parameters_five_split.append((day, trace_id, core, slack_set, set_num, [i / 10 for i in range(9, 10)]))
            # nine split - all slacks have their individual core
            if day in nine_split:
                parameters_nine_split.append((day, trace_id, core, slack_set, set_num, [i / 10 for i in range(1, 2)]))
                parameters_nine_split.append((day, trace_id, core, slack_set, set_num, [i / 10 for i in range(2, 3)]))
                parameters_nine_split.append((day, trace_id, core, slack_set, set_num, [i / 10 for i in range(3, 4)]))
                parameters_nine_split.append((day, trace_id, core, slack_set, set_num, [i / 10 for i in range(4, 5)]))
                parameters_nine_split.append((day, trace_id, core, slack_set, set_num, [i / 10 for i in range(5, 6)]))
                parameters_nine_split.append((day, trace_id, core, slack_set, set_num, [i / 10 for i in range(6, 7)]))
                parameters_nine_split.append((day, trace_id, core, slack_set, set_num, [i / 10 for i in range(7, 8)]))
                parameters_nine_split.append((day, trace_id, core, slack_set, set_num, [i / 10 for i in range(8, 9)]))
                parameters_nine_split.append((day, trace_id, core, slack_set, set_num, [i / 10 for i in range(9, 10)]))

            # sd split into 3 groups - 4 sd ranges each for each slack
            if day in sd_split_four:
                slacks = [i / 10 for i in range(1, 10)]
                for slack in slacks:
                    parameters_sd_split_four.append((day, trace_id, core, slack_set, set_num,
                                                     [slack], [i / 10 for i in range(30, 26, -1)]))
                    parameters_sd_split_four.append((day, trace_id, core, slack_set, set_num,
                                                     [slack], [i / 10 for i in range(26, 22, -1)]))
                    parameters_sd_split_four.append((day, trace_id, core, slack_set, set_num,
                                                     [slack], [i / 10 for i in range(22, 19, -1)]))
            # sd split into 6 groups - 2 sd ranges each for each slack
            if day in sd_split_two:
                slacks = [i / 10 for i in range(1, 10)]
                for slack in slacks:
                    parameters_sd_split_two.append((day, trace_id, core, slack_set, set_num,
                                                    [slack], [i / 10 for i in range(30, 28, -1)]))
                    parameters_sd_split_two.append((day, trace_id, core, slack_set, set_num,
                                                    [slack], [i / 10 for i in range(28, 26, -1)]))
                    parameters_sd_split_two.append((day, trace_id, core, slack_set, set_num,
                                                    [slack], [i / 10 for i in range(26, 24, -1)]))
                    parameters_sd_split_two.append((day, trace_id, core, slack_set, set_num,
                                                    [slack], [i / 10 for i in range(24, 22, -1)]))
                    parameters_sd_split_two.append((day, trace_id, core, slack_set, set_num,
                                                    [slack], [i / 10 for i in range(22, 20, -1)]))
                    parameters_sd_split_two.append((day, trace_id, core, slack_set, set_num,
                                                    [slack], [i / 10 for i in range(20, 19, -1)]))
            # sd split into 11 groups - each sd separately for each slack
            if day in sd_split_one:
                for slack in SLACKS:
                    for sd in SD:
                        parameters_sd_split_one.append((day, trace_id, core, slack_set, set_num, [slack], [sd]))

        return parameters_no_split + parameters_two_split + parameters_three_split + parameters_five_split +\
            parameters_nine_split + parameters_sd_split_four + parameters_sd_split_two + parameters_sd_split_one

    @staticmethod
    def generate_batches(lido_parameters, lido_cores):
        parameters_batch = []
        for index in range(0, len(lido_parameters), lido_cores):
            end_index = index + lido_cores
            if end_index > len(lido_parameters):
                end_index = len(lido_parameters)
            parameters_batch.append(lido_parameters[index:end_index])
        return parameters_batch

    @staticmethod
    def c302019anp(trace_id, core, slack_set, set_num, lido_cores):
        # split defined for all 31 days
        no_split = [2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 14, 16, 17, 18, 19]
        two_split = [13, 15, 20]
        three_split = [1, 10, 21, 22, 24, 25, 26, 27, 28, 29]
        five_split = [23]
        nine_split = [30]
        sd_split_four = [31]
        sd_split_two = []
        sd_split_one = []

        lido_parameters = Lido.parallelization_parameters(trace_id, core, slack_set, set_num,
                                                          no_split, two_split, three_split, five_split, nine_split,
                                                          sd_split_four, sd_split_two, sd_split_one)
        return Lido.generate_batches(lido_parameters, lido_cores)

    @staticmethod
    def c1202019anp(trace_id, core, slack_set, set_num, lido_cores):
        no_split = []
        two_split = [2, 3, 4, 5, 6, 9, 11, 12, 18, 19]
        three_split = [7, 8, 13, 15, 16, 17, 20]
        five_split = [10, 14]
        nine_split = [1, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]
        sd_split_four = []
        sd_split_two = []
        sd_split_one = [31]

        lido_parameters = Lido.parallelization_parameters(trace_id, core, slack_set, set_num,
                                                          no_split, two_split, three_split, five_split, nine_split,
                                                          sd_split_four, sd_split_two, sd_split_one)
        return Lido.generate_batches(lido_parameters, lido_cores)

    @staticmethod
    def c1202019ap(trace_id, core, slack_set, set_num, lido_cores):
        no_split = [2, 3, 4, 5, 6, 7, 8, 9,
                    10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
        two_split = [1, 29]
        three_split = [20, 24, 25, 26, 27, 28]
        five_split = [21, 22, 23]
        nine_split = [30]
        sd_split_four = []
        sd_split_two = []
        sd_split_one = [31]

        lido_parameters = Lido.parallelization_parameters(trace_id, core, slack_set, set_num,
                                                          no_split, two_split, three_split, five_split, nine_split,
                                                          sd_split_four, sd_split_two, sd_split_one)
        return Lido.generate_batches(lido_parameters, lido_cores)

    @staticmethod
    def test(trace_id, core, slack_set, set_num, lido_cores):
        no_split = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
                    11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                    21, 22, 23, 24, 25, 26, 27, 28, 29, 30,
                    31]
        two_split = []
        three_split = []
        five_split = []
        nine_split = []
        sd_split_four = []
        sd_split_two = []
        sd_split_one = []

        lido_parameters = Lido.parallelization_parameters(trace_id, core, slack_set, set_num,
                                                          no_split, two_split, three_split, five_split, nine_split,
                                                          sd_split_four, sd_split_two, sd_split_one)
        return Lido.generate_batches(lido_parameters, lido_cores)
