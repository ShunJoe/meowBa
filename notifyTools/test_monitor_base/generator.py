import numpy as np
import random
import foam_ct_phantom as foam_ct_phantom

def generate_foam(nspheres_per_unit, vx, vy, vz, res):
    def maxsize_func(x, y, z):
        return 0.2 - 0.1*np.abs(z)

    random_seed=random.randint(0,4294967295)
    foam_ct_phantom.FoamPhantom.generate('temp_phantom_info.h5',
                                         random_seed,
                                         nspheres_per_unit=nspheres_per_unit,
                                         maxsize=maxsize_func)

    geom = foam_ct_phantom.VolumeGeometry(vx, vy, vz, res)
    phantom = foam_ct_phantom.FoamPhantom('temp_phantom_info.h5')
    phantom.generate_volume('temp_phantom.h5', geom)
    dataset = foam_ct_phantom.load_volume('temp_phantom.h5')

    return dataset

def create_foam_data_file(filename:str, val:int, vx:int, vy:int, vz:int, res:int):
    dataset = generate_foam(val, vx, vy, vz, res)
    np.save(filename, dataset)
    del dataset