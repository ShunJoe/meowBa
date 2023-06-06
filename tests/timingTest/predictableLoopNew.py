import os
import random
import importlib.util
from multiprocessing import Pool, cpu_count
import shutil
import yaml
from typing import List

import yaml
from os import makedirs, remove, rmdir, walk
from os.path import exists, isfile, join

def make_dir(path:str, can_exist:bool=True, ensure_clean:bool=False):
    """
    Creates a new directory at the given path.

    :param path: (str) The directory path.

    :param can_exist: (boolean) [optional] A toggle for if a previously
    existing directory at the path will throw an error or not. Default is
    true (e.g. no error is thrown if the path already exists)

    :param ensure_clean: (boolean) [optional] A toggle for if a previously
    existing directory at the path will be replaced with a new emtpy directory.
    Default is False.

    :return: No return
    """
    if exists(path):
        if isfile(path):
            raise ValueError(
                f"Cannot make directory in {path} as it already exists and is "
                "a file")
        if ensure_clean:
            rmtree(path)
                
    makedirs(path, exist_ok=can_exist)

def rmtree(directory:str):
    """
    Remove a directory and all its contents. 
    Should be faster than shutil.rmtree
    
    :param: (str) The firectory to empty and remove

    :return: No return
    """
    if not exists(directory):
        return
    for root, dirs, files in walk(directory, topdown=False):
        for file in files:
            remove(join(root, file))
        for dir in dirs:
            rmtree(join(root, dir))
    rmdir(directory)

def lines_to_string(lines:List[str])->str:
    """Function to convert a list of str lines, into one continuous string 
    separated by newline characters"""
    return "\n".join(lines)

GENERATE_PYTHON_SCRIPT = [
    "import numpy as np",
    "import random",
    "import foam_ct_phantom as foam_ct_phantom",
    "",
    "def generate_foam(nspheres_per_unit, vx, vy, vz, res):",
    "    def maxsize_func(x, y, z):",
    "        return 0.2 - 0.1*np.abs(z)",
    "",
    "    random_seed=random.randint(0,4294967295)",
    "    foam_ct_phantom.FoamPhantom.generate('temp_phantom_info.h5',",
    "                                         random_seed,",
    "                                         nspheres_per_unit=nspheres_per_unit,",
    "                                         maxsize=maxsize_func)",
    "",
    "    geom = foam_ct_phantom.VolumeGeometry(vx, vy, vz, res)",
    "    phantom = foam_ct_phantom.FoamPhantom('temp_phantom_info.h5')",
    "    phantom.generate_volume('temp_phantom.h5', geom)",
    "    dataset = foam_ct_phantom.load_volume('temp_phantom.h5')",
    "",
    "    return dataset",
    "",
    "def create_foam_data_file(filename:str, val:int, vx:int, vy:int, vz:int, res:int):",
    "    dataset = generate_foam(val, vx, vy, vz, res)",
    "    np.save(filename, dataset)",
    "    del dataset"
]

TEST_DIR = "test_files"
TEST_MONITOR_BASE = "test_monitor_base"
TEST_JOB_QUEUE = "test_job_queue_dir"
TEST_JOB_OUTPUT = "test_job_output"
TEST_DATA = "test_data"

def setup():
    make_dir(TEST_DIR, ensure_clean=True)
    make_dir(TEST_MONITOR_BASE, ensure_clean=True)
    make_dir(TEST_JOB_QUEUE, ensure_clean=True)
    make_dir(TEST_JOB_OUTPUT, ensure_clean=True)

# Initializing some variables
good = 10
big = 5
small = 0
vx = 64
vy = 64
vz = 64
res = 3/vz
backup_data_dir = os.path.join(TEST_DATA, "foam_ct_data")
os.makedirs(backup_data_dir, exist_ok=True)
foam_data_dir = os.path.join(TEST_MONITOR_BASE, "foam_ct_data")
os.makedirs(foam_data_dir, exist_ok=True)

# Assuming that lines_to_string and GENERATE_PYTHON_SCRIPT are predefined
gen_path = os.path.join(TEST_MONITOR_BASE, "generator.py")
with open(gen_path, 'w') as f:
    f.write(lines_to_string(GENERATE_PYTHON_SCRIPT))

all_data = [1000] * good + [100] * big + [10000] * small
random.shuffle(all_data)

u_spec = importlib.util.spec_from_file_location("gen", gen_path)
gen = importlib.util.module_from_spec(u_spec)
u_spec.loader.exec_module(gen)

for i, val in enumerate(all_data):
    filename = f"foam_dataset_{i}_{val}_{vx}_{vy}_{vz}.npy"
    backup_file = os.path.join(backup_data_dir, filename)

    # You will need to implement 'gen.create_foam_data_file()' in your 'generator.py' script.
    if not os.path.exists(backup_file):
        gen.create_foam_data_file(backup_file, val, vx, vy, vz, res)

    target_file = os.path.join(foam_data_dir, filename)
    os.system(f"cp {backup_file} {target_file}")  # copying files

# Here we're using multiprocessing to mimic the runner.start() functionality
with Pool(cpu_count()) as p:
    data_files = os.listdir(foam_data_dir)
    p.map(analyze_data, data_files)  # assuming each data file can be analyzed independently

# Error checking and assertions
job_output_dir = TEST_JOB_OUTPUT
jobs = len(os.listdir(job_output_dir))
expected_jobs = good * 3 + big * 5 + small * 5
assert jobs == expected_jobs, "Number of jobs does not match expected count."

for job_dir in os.listdir(job_output_dir):
    metafile = os.path.join(job_output_dir, job_dir, "metafile.yml")  # assuming this file exists

    with open(metafile, 'r') as f:
        status = yaml.load(f, Loader=yaml.FullLoader)

    if "error" in status:  # assuming 'error' key exists in the yaml file when there's an error
        print(status["error"])
        for dir_to_backup in [job_output_dir, TEST_JOB_QUEUE, TEST_MONITOR_BASE]:
            shutil.copytree(dir_to_backup, f"Backup-predictable-{dir_to_backup}")

    assert "error" not in status, "Error found in job."

    result_path = os.path.join(job_output_dir, job_dir, "result.ipynb")
    assert os.path.exists(result_path), "Result file does not exist."

results_dir = os.path.join(TEST_MONITOR_BASE, "foam_ct_data_pore_analysis")
results = len(os.listdir(results_dir))
assert results == good + big + small, "Number of results does not match expected count."