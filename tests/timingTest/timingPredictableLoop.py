import os
import random
import importlib.util
from typing import List
from nbconvert.preprocessors import ExecutePreprocessor

import nbformat as nbf

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
TEST_MONITOR = "test_monitor"
TEST_JOB_QUEUE = "test_job_queue_dir"
TEST_JOB_OUTPUT = "test_job_output"
BACKUP_DATA = "backup_data"

def create_notebook(data_file):
    nb = nbf.v4.new_notebook()

    # Import necessary modules
    import_cell = nbf.v4.new_code_cell("import numpy as np\nimport matplotlib.pyplot as plt\nimport os\nimport importlib.util\nfrom skimage.feature import peak_local_max\nfrom skimage.morphology import watershed\nfrom scipy import ndimage as snd\nfrom matplotlib.colors import ListedColormap\nfrom matplotlib import cm")
    nb.cells.append(import_cell)

    # Define the analyze_data function
    analyze_data_cell = nbf.v4.new_code_cell("""def analyze_data(input_filename):
    # Load data
    data = np.load(input_filename)

    # Watershed: Identify separate pores
    distance = snd.distance_transform_edt((data == 0))
    local_maxi = peak_local_max(distance, indices=False, footprint=np.ones((3, 3, 3)), labels=(data == 0))
    markers = snd.label(local_maxi)[0]
    labels = watershed(-distance, markers, mask=(data == 0))

    # Pore color map
    somecmap = cm.get_cmap('magma', 256)
    cvals = np.random.uniform(0, 1, len(np.unique(labels)))
    newcmp = ListedColormap(somecmap(cvals))

    # Plot statistics: pore radii
    volumes = np.array([np.sum(labels == label) for label in np.unique(labels)])
    volumes.sort()
    # Ignore two largest labels (background and matrix)
    radii = (volumes[:-2] * 3 / (4 * np.pi)) ** (1 / 3)  # Find radii, assuming spherical pores
    _ = plt.hist(radii, bins=200)

    # Save plot
    filename_without_npy = input_filename.split(os.path.sep)[-1].split('.')[0]
    filename_save = filename_without_npy + '_statistics.png'
    output_filedir = "test_job_output"  # specify your output directory here

    os.makedirs(output_filedir, exist_ok=True)
    plt.savefig(os.path.join(output_filedir, filename_save))""")
    nb.cells.append(analyze_data_cell)

    # Define the check_porosity function
    check_porosity_cell = nbf.v4.new_code_cell("""def check_porosity(input_filename):
    input_filename = input_filename
    output_filedir_accepted = 'foam_ct_data_accepted'
    output_filedir_discarded = 'foam_ct_data_discarded'
    porosity_lower_threshold = 0.8
    utils_path = '../idmc_utils_module.py'

    # Load the custom utils module
    spec = importlib.util.spec_from_file_location("utils", utils_path)
    utils = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(utils)

    # Parameters
    n_samples = 10000

    # Load data
    ct_data = np.load(input_filename)

    # Plot center slices
    utils.plot_center_slices(ct_data)

    # Perform GMM fitting on samples from the dataset
    sample_inds = np.random.randint(0, len(ct_data.ravel()), n_samples)
    n_components = 2
    means, stds, weights = utils.perform_GMM_np(
        ct_data.ravel()[sample_inds],
        n_components,
        plot=True,
        title='GMM fitted to ' + str(n_samples) + ' of ' +
        str(len(ct_data.ravel())) + ' datapoints')
    print('weights:', weights)

    # Classify data as 'accepted' or 'discarded' according to porosity level
    filename_without_npy = input_filename.split(os.path.sep)[-1].split('.')[0]

    if np.max(weights) > porosity_lower_threshold:
        os.makedirs(output_filedir_accepted, exist_ok=True)
        acc_path = os.path.join(output_filedir_accepted, filename_without_npy + '.txt')
        with open(acc_path, 'w') as file:
            file.write(str(np.max(weights)) + ' ' + str(np.min(weights)))
    else:
        os.makedirs(output_filedir_discarded, exist_ok=True)
        dis_path = os.path.join(output_filedir_discarded, filename_without_npy + '.txt')
        with open(dis_path, 'w') as file:
            file.write(str(np.max(weights)) + ' ' + str(np.min(weights)))""")
    nb.cells.append(check_porosity_cell)

    # Call the functions for the specific data_file
    call_functions_cell = nbf.v4.new_code_cell(f"""analyze_data('{data_file}') \ncheck_porosity('{data_file}')""")
    nb.cells.append(call_functions_cell)

    # Save the notebook file
    output_dir = "generated_notebooks"  # specify the directory where you want to save the generated notebooks
    os.makedirs(output_dir, exist_ok=True)
    notebook_path = os.path.join(output_dir, f"{data_file.split(os.path.sep)[-1].split('.')[0]}.ipynb")
    nbf.write(nb, notebook_path)


def setup():
    make_dir(TEST_DIR, ensure_clean=True)
    make_dir(TEST_MONITOR, ensure_clean=True)
    make_dir(TEST_JOB_QUEUE, ensure_clean=True)
    make_dir(TEST_JOB_OUTPUT, ensure_clean=True)
    make_dir(BACKUP_DATA, ensure_clean=False)
# Initializing some variables
good = 10
big = 5
small = 0
vx = 64
vy = 64
vz = 64
res = 3/vz
backup_data_dir = os.path.join(BACKUP_DATA, "foam_ct_data")
make_dir(backup_data_dir, ensure_clean=False)
foam_data_dir = os.path.join(TEST_MONITOR, "foam_ct_data")
make_dir(foam_data_dir, ensure_clean=False)

# Assuming that lines_to_string and GENERATE_PYTHON_SCRIPT are predefined
gen_path = "generator.py"
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

# Code part where the functions are called
data_files = os.listdir(foam_data_dir)
data_files = [os.path.join(foam_data_dir, f) for f in data_files]

for data_file in data_files:
    create_notebook(os.path.join("../", data_file))

def run_notebook(notebook_path):
    # Load the notebook
    with open(notebook_path, "r", encoding="utf-8") as f:
        nb = nbf.read(f, as_version=4)

    # Create an instance of the ExecutePreprocessor
    ep = ExecutePreprocessor(timeout=None)

    # Execute the notebook
    ep.preprocess(nb, {"metadata": {"path": os.path.dirname(notebook_path)}})

    # Save the executed notebook
    with open(notebook_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)

# Specify the directory where the notebooks are located
notebooks_dir = "generated_notebooks"

# Get the list of notebook files in the directory
notebook_files = [f for f in os.listdir(notebooks_dir) if f.endswith(".ipynb")]

# Run each notebook file
for notebook_file in notebook_files:
    notebook_path = os.path.join(notebooks_dir, notebook_file)
    run_notebook(notebook_path)

#data_files = os.listdir(foam_data_dir)
#data_files = [os.path.join("backup_data/foam_ct_data/", f) for f in data_files]
#for i in range(len(data_files)):
#    analyze_data(data_files[i])  # assuming each data file can be analyzed independently
#    check_porosity(data_files[i])
# Error checking and assertions
# job_output_dir = TEST_JOB_OUTPUT
# jobs = len(os.listdir(job_output_dir))
# expected_jobs = good * 3 + big * 5 + small * 5
# assert jobs == expected_jobs, "Number of jobs does not match expected count."

# results_dir = os.path.join(TEST_MONITOR, "foam_ct_data_pore_analysis")
# results = len(os.listdir(results_dir))
# assert results == good + big + small, "Number of results does not match expected count."