from schedulingelements import Job, Container, Machine
from functions import FileOperations

if __name__ == '__main__':
    print('Test file.')

    j1 = Job("J1", 10, 0, 13, 1)
    j2 = Job("J2", 5, 11, 20, 1)
    j1.update(2, 12)
    j2.update(12, 17)
    c1 = Container('C1', j1, 2, 12)
    c2 = Container('C2', j2, 12, 17)

    m = Machine()
    m.update(c1, 12)
    m.update(c2, 17)

    m.print_schedule()
    print(m.get_available_time())

    file = FileOperations()
    file.test()







def _read_jobs(file_path):
    with open(file_path) as file:
        content = file.readlines()

    job_list = []
    for data in content:
        values = data.strip().split(";")

