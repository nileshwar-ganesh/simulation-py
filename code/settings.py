# -----------------------------------------------------------------------------------------
# PATHS
PROJECT_FOLDER_PATH = '/home/nileshwar-gk/Projects/simulation-py/'
SOURCE_FOLDER_PATH = '/home/nileshwar-gk/Projects/simulation-py/'

CLOUD_TRACE_FOLDER = {'2011': SOURCE_FOLDER_PATH + 'cloudjobs/google2011/',
                      '2019A': SOURCE_FOLDER_PATH + 'cloudjobs/google2019a/'}

SLACK_FOLDER = {'JV': SOURCE_FOLDER_PATH + 'lognormalslacks/JAVA/',
                'MA': SOURCE_FOLDER_PATH + 'lognormalslacks/MATLAB/',
                'PY': SOURCE_FOLDER_PATH + 'lognormalslacks/PYTHON/'}

STATISTICAL_TRACE_FOLDER = PROJECT_FOLDER_PATH + 'statisticaltraces/'
RESULT_FOLDER = PROJECT_FOLDER_PATH + 'results/'
LOG_FOLDER = PROJECT_FOLDER_PATH + 'log/'

TEST_DATA = PROJECT_FOLDER_PATH + 'testdata/jobs.txt'
# -----------------------------------------------------------------------------------------

# -----------------------------------------------------------------------------------------
# SIMULATION SETTING
DAYS = {'2011': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
                 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                 21, 22, 23, 24, 25, 26, 27, 28, 29],
        '2019A': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
                  11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                  21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31]
        }

SETS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
SLACKS = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
SD = [3.0, 2.9, 2.8, 2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0]

MI2011 = {1: 10, 30: 20, 120: 50, 500: 100, 5000: 200}
RAW = {'2011': 'GoogleTrace', '2019A': 'GoogleTrace2019'}
TRACE = {'2011': "GoogleTrace2011", '2019A': "GoogleTrace2019A"}

# MACHINE SETTINGS
MACHINE_START = {'2019A': {1: 50, 30: 100, 120: 200, 5000: 1000}}

MACHINE_END = {'2019A': {1: {1: 900, 2: 560, 3: 560, 4: 560, 5: 390, 6: 730, 7: 730, 8: 560, 9: 560, 10: 560,
                             11: 390, 12: 560, 13: 560, 14: 560, 15: 560, 16: 560, 17: 560, 18: 560, 19: 560, 20: 730,
                             21: 730, 22: 730, 23: 730, 24: 730, 25: 730, 26: 730, 27: 560, 28: 730, 29: 730, 30: 1070,
                             31: 2090}
                         }
               }

MACHINE_INCREMENT = {'2019A': {1: {1: 50, 2: 30, 3: 30, 4: 30, 5: 20, 6: 40, 7: 40, 8: 30, 9: 30, 10: 30,
                                   11: 20, 12: 30, 13: 30, 14: 30, 15: 30, 16: 30, 17: 30, 18: 30, 19: 30, 20: 40,
                                   21: 40, 22: 40, 23: 40, 24: 40, 25: 40, 26: 40, 27: 30, 28: 40, 29: 40, 30: 60,
                                   31: 120}
                               }
                     }
