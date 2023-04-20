import os
import multiprocessing

def create_files_and_dirs(i):
    dir_path = f"dir{i}"
    os.mkdir(dir_path)
    os.mkdir(f"{dir_path}copy")
    open(f"file{i}", "w").close()
    open(f"file{i}copy", "w").close()
    os.remove(f"file{i}")
    os.remove(f"file{i}copy")
    os.rmdir(f"{dir_path}copy")
    os.rmdir(dir_path)

if __name__ == "__main__":
    j = 1000000
    with multiprocessing.Pool(processes=2) as pool:
        pool.map(create_files_and_dirs, range(1, j+1))
