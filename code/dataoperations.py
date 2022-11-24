import os
from code.settings import CLOUD_TRACE_FOLDER

# Summarize cloud traces
def generate_data_tables(trace_id):
    read_folder = CLOUD_TRACE_FOLDER[trace_id]
    contents = []
    if os.path.exists(read_folder):
        contents = os.listdir(read_folder)

    while len(contents) > 0:
        content = contents.pop()
        with open(os.path.join(read_folder, content)) as file:
            job_data = file.readlines()

        for line in job_data:
            data = line.strip().split('\t')





