import os
import multiprocessing

def create_files_and_dirs(i):
    dir_path = f"dir{i}"
    os.mkdir(dir_path)
    os.mkdir(f"copy{dir_path}")
    open(f"file{i}", "w").close()
    open(f"filecopy{i}", "w").close()
    os.remove(f"file{i}")
    os.remove(f"filecopy{i}")
    os.rmdir(f"copy{dir_path}")
    os.rmdir(dir_path)

if __name__ == "__main__":
    j = 1000
    with multiprocessing.Pool(processes=2) as pool:
        pool.map(create_files_and_dirs, range(1, j+1))
