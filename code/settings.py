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

MACHINE_END = {'2019A': {1: {1: 970, 2: 570, 3: 680, 4: 510, 5: 470, 6: 710, 7: 770, 8: 680, 9: 680, 10: 680,
                             11: 470, 12: 510, 13: 680, 14: 680, 15: 680, 16: 680, 17: 680, 18: 510, 19: 510, 20: 710,
                             21: 710, 22: 710, 23: 710, 24: 710, 25: 710, 26: 710, 27: 680, 28: 770, 29: 770, 30: 1150,
                             31: 2750}
                         }
               }

MACHINE_INCREMENT = {'2019A': {1: {1: 40, 2: 20, 3: 30, 4: 20, 5: 20, 6: 30, 7: 30, 8: 30, 9: 30, 10: 30,
                                   11: 20, 12: 20, 13: 30, 14: 30, 15: 30, 16: 30, 17: 30, 18: 20, 19: 20, 20: 30,
                                   21: 30, 22: 30, 23: 30, 24: 30, 25: 30, 26: 30, 27: 30, 28: 30, 29: 30, 30: 50,
                                   31: 100}
                               }
                     }
