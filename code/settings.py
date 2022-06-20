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

MACHINE_END = {'2019A': {1: {1: 900, 2: 560, 3: 730, 4: 560, 5: 560,
                             6: 730, 7: 730, 8: 730, 9: 730, 10: 730,
                             11: 560, 12: 560, 13: 730, 14: 730, 15: 730,
                             16: 730, 17: 730, 18: 560, 19: 560, 20: 730,
                             21: 730, 22: 730, 23: 730, 24: 730, 25: 730,
                             26: 730, 27: 730, 28: 730, 29: 730, 30: 1070,
                             31: 2260},
                         30: {1: 5200, 2: 1630, 3: 1630, 4: 1460, 5: 1290,
                              6: 1800, 7: 1970, 8: 1800, 9: 1800, 10: 2140,
                              11: 1120, 12: 1460, 13: 1800, 14: 1630, 15: 1970,
                              16: 1630, 17: 1630, 18: 1630, 19: 1460, 20: 1800,
                              21: 1800, 22: 1800, 23: 2310, 24: 2140, 25: 1800,
                              26: 1970, 27: 1970, 28: 2140, 29: 1970, 30: 2650,
                              31: 5880},
                         120: {1: 8530, 2: 2580, 3: 2920, 4: 2750, 5: 2410,
                               6: 3260, 7: 3770, 8: 3600, 9: 3090, 10: 3600,
                               11: 2410, 12: 2920, 13: 3430, 14: 3770, 15: 3260,
                               16: 3260, 17: 2920, 18: 2580, 19: 2240, 20: 3260,
                               21: 3090, 22: 3260, 23: 4280, 24: 3940, 25: 3260,
                               26: 3430, 27: 3430, 28: 4110, 29: 4110, 30: 4110,
                               31: 11080}
                         }
               }

MACHINE_INCREMENT = {'2019A': {1: {1: 50, 2: 30, 3: 40, 4: 30, 5: 30,
                                   6: 40, 7: 40, 8: 40, 9: 40, 10: 40,
                                   11: 30, 12: 30, 13: 40, 14: 40, 15: 40,
                                   16: 40, 17: 40, 18: 30, 19: 30, 20: 40,
                                   21: 40, 22: 40, 23: 40, 24: 40, 25: 40,
                                   26: 40, 27: 40, 28: 40, 29: 40, 30: 60,
                                   31: 130},
                               30: {1: 300, 2: 90, 3: 90, 4: 80, 5: 70,
                                    6: 100, 7: 110, 8: 100, 9: 100, 10: 120,
                                    11: 60, 12: 80, 13: 100, 14: 90, 15: 110,
                                    16: 90, 17: 90, 18: 90, 19: 80, 20: 100,
                                    21: 100, 22: 100, 23: 130, 24: 120, 25: 100,
                                    26: 110, 27: 110, 28: 120, 29: 110, 30: 150,
                                    31: 340},
                               120: {1: 490, 2: 140, 3: 160, 4: 150, 5: 130,
                                     6: 180, 7: 210, 8: 200, 9: 170, 10: 200,
                                     11: 130, 12: 160, 13: 190, 14: 210, 15: 180,
                                     16: 180, 17: 160, 18: 140, 19: 120, 20: 180,
                                     21: 170, 22: 180, 23: 240, 24: 220, 25: 180,
                                     26: 190, 27: 190, 28: 230, 29: 230, 30: 230,
                                     31: 640},
                               }
                     }
