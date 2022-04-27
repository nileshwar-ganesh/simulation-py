from settings import CLOUD_TRACE_FOLDER, SLACK_FOLDER, STATISTICAL_TRACE_FOLDER
from settings import RESULT_FOLDER, LOG_FOLDER

class FileOperations:
    
    def __init__(self):
        self.trace_folder = CLOUD_TRACE_FOLDER
        self.slack_folder = SLACK_FOLDER
        self.statistical_trace_folder = STATISTICAL_TRACE_FOLDER
        self.result_folder = RESULT_FOLDER
        self.log_folder = LOG_FOLDER

    def test(self):
        file_address = self.trace_folder + "testfile.txt"
        self.dummy_write(file_address)

        file_address = self.slack_folder + "testfile.txt"
        self.dummy_write(file_address)

        file_address = self.statistical_trace_folder + "testfile.txt"
        self.dummy_write(file_address)

        file_address = self.result_folder + "testfile.txt"
        self.dummy_write(file_address)

        file_address = self.log_folder + "testfile.txt"
        self.dummy_write(file_address)

    def dummy_write(self, file_address):
        file = open(file_address, "w")
        file.write("Testing...")
        file.close()

    def generate_trace_single_day(self, day_nr):
        trace_file = self.trace_folder + '/Day' + day_nr + '/'
