# -----------------------------------------------------------------------------------------
# PATHS
CLOUD_TRACE_FOLDER = {'2011': '/home/nileshwar-gk/Projects/cloud-jobs/google-2011/',
                      '2019A': '/home/nileshwar-gk/Projects/cloud-jobs/google-2019-a/'}

SLACK_FOLDER = {'JV': '/home/nileshwar-gk/Projects/statistical-traces/lognormal-slacks/JAVA/',
                'MA': '/home/nileshwar-gk/Projects/statistical-traces/lognormal-slacks/MATLAB/',
                'PY': '/home/nileshwar-gk/Projects/statistical-traces/lognormal-slacks/PYTHON/'}

STATISTICAL_TRACE_FOLDER= '/home/nileshwar-gk/Projects/statistical-traces/'
RESULT_FOLDER = '/home/nileshwar-gk/Projects/simulation-py/results/'
LOG_FOLDER = '/home/nileshwar-gk/Projects/simulation-py/log/'

TEST_DATA = '/home/nileshwar-gk/Projects/simulation-py/testdata/jobs.txt'
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
SD = [3.0, 2.0, 2.8, 2.7, 2.6, 2.5, 2.4, 2.3, 2.2, 2.1, 2.0]

MI2011 = {1: 10, 30: 20, 120: 50, 500: 100, 5000: 200}
RAW = {'2011': 'GoogleTrace', '2019A': 'GoogleTrace2019'}
TRACE = {'2011': "GoogleTrace2011", '2019A': "GoogleTrace2019A"}

C1 = {1: 100, 2: 100, 3: 100}
