import importlib
import os
import unittest

from multiprocessing import Pipe
from random import shuffle
from shutil import copy
from warnings import warn

good = 10
big = 5
small = 0
vx = 64
vy = 64
vz = 64
res = 3/vz
all_data = [1000] * good + [100] * big + [10000] * small
shuffle(all_data)
gen_path = os.path.join("./", "generator.py")

u_spec = importlib.util.spec_from_file_location("gen", gen_path)
gen = importlib.util.module_from_spec(u_spec)
u_spec.loader.exec_module(gen)
foam_data_dir = os.path.join("./", "foam_ct_data")

backup_data_dir = os.path.join("./", "backup")


for i, val in enumerate(all_data):
    filename = f"foam_dataset_{i}_{val}_{vx}_{vy}_{vz}.npy"
    backup_file = os.path.join(backup_data_dir, filename)
    if not os.path.exists(backup_file):
        gen.create_foam_data_file(backup_file, val, vx, vy, vz, res)
        target_file = os.path.join(foam_data_dir, filename)
        copy(backup_file, target_file)

input_filename = 'foam_ct_data/foam_dataset_16_100_32_32_32.npy'
input_filedir = 'foam_ct_data'
output_filedir = 'foam_ct_data_segmented'
utils_path = 'idmc_utils_module.py'

import numpy as np
import importlib
import matplotlib.pyplot as plt
import os
import scipy.ndimage as snd
import skimage

import importlib.util
spec = importlib.util.spec_from_file_location("utils", utils_path)
utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utils)

# Parameters
median_filter_kernel_size = 2

# Load data
filename_withouth_txt = input_filename.split(os.path.sep)[-1].split('.')[0]
input_data = os.path.join(input_filedir, filename_withouth_txt+'.npy')
ct_data = np.load(input_data)
utils.plot_center_slices(ct_data, title=filename_withouth_txt)

# Median filtering
data_filtered = snd.median_filter(ct_data, median_filter_kernel_size)
utils.plot_center_slices(data_filtered, title=filename_withouth_txt+' median filtered')

# Otsu thresholding
threshold = skimage.filters.threshold_otsu(data_filtered)
data_thresholded = (data_filtered > threshold) * 1
utils.plot_center_slices(data_thresholded, title=filename_withouth_txt+' Otsu thresholded')

# Morphological closing
data_segmented = (skimage.morphology.binary_closing((data_thresholded == 0)) == 0)
utils.plot_center_slices(data_segmented, title=filename_withouth_txt+' Otsu thresholded')

# Save data
filename_save = filename_withouth_txt+'_segmented.npy'
os.makedirs(output_filedir, exist_ok=True)
np.save(os.path.join(output_filedir, filename_save), data_segmented)

# Variables that will be overwritten according to the pattern
input_filename = 'foam_ct_data_segmented/foam_dataset_16_100_32_32_32_segmented.npy'
output_filedir = 'foam_ct_data_pore_analysis'
utils_path = 'idmc_utils_module.py'

import numpy as np
import importlib
import matplotlib.pyplot as plt
import os
import scipy.ndimage as snd

from skimage.segmentation import watershed
from skimage.feature import peak_local_max
from matplotlib import cm
from matplotlib.colors import ListedColormap, LinearSegmentedColormap

import importlib.util
spec = importlib.util.spec_from_file_location("utils", utils_path)
utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utils)

# Load data
data = np.load(input_filename)
utils.plot_center_slices(data, title=input_filename)

# Watershed: Identify separate pores
distance = snd.distance_transform_edt((data == 0))
local_maxi = peak_local_max(distance, indices=False, footprint=np.ones((3, 3, 3)), labels=(data == 0))
markers = snd.label(local_maxi)[0]
labels = watershed(-distance, markers, mask=(data == 0))

# Pore color map
somecmap = cm.get_cmap('magma', 256)
cvals = np.random.uniform(0, 1, len(np.unique(labels)))
newcmp = ListedColormap(somecmap(cvals))

utils.plot_center_slices(-distance, cmap=plt.cm.gray, title='Distances')
utils.plot_center_slices(labels, cmap=newcmp, title='Separated pores')

# Plot statistics: pore radii
volumes = np.array([np.sum(labels == label) for label in np.unique(labels)])
volumes.sort()
# Ignore two largest labels (background and matrix)
radii = (volumes[:-2] * 3 / (4 * np.pi)) ** (1 / 3)  # Find radii, assuming spherical pores
_ = plt.hist(radii, bins=200)

# Save plot
filename_withouth_npy = input_filename.split(os.path.sep)[-1].split('.')[0]
filename_save = filename_withouth_npy + '_statistics.png'

fig, ax = plt.subplots(1, 3, figsize=(15, 4))
ax[0].imshow(labels[:, :, np.shape(labels)[2] // 2], cmap=newcmp)
ax[1].imshow(labels[:, np.shape(labels)[2] // 2, :], cmap=newcmp)
_ = ax[2].hist(radii, bins=200)
ax[2].set_title('Foam pore radii')

os.makedirs(output_filedir, exist_ok=True)
plt.savefig(os.path.join(output_filedir, filename_save))
