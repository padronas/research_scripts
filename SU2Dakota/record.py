
import json
import os
import numpy as np
from SU2.util.bunch import *


class Record(Bunch):
  """Starts a new Record class, an extension of Bunch

    use 1: initialize empty
    use 2: initialize by a record file json

  """

  def __init__(self, filename, config):
    if os.path.isfile(filename):
        print 'Loading record of simulations'
        record_file = open(filename,'r')
        record_dict = json.load(record_file)
        self.update(bunchify(record_dict))
        record_file.close()
    else:
        print 'Creating new record of simulations'
        self.simulations = Bunch()
        mesh_filename = config.MESH_FILENAME
        head, tail = os.path.split(os.getcwd())
        self.baseline_mesh = head + '/' + mesh_filename
        self.current_mesh = self.baseline_mesh

  def deform_needed(self,x):
    '''Checks if mesh deformation needed.'''

    i = self.nsimulations
    current_simulation = 'simulation' + str(i)

    # Don't deform, if I already deformed mesh for the current simulation.
    if self.simulations[current_simulation].mesh_updated:
        return False

    # Don't deform, if design vector is zero or same as previous simulation.
    if np.linalg.norm(x) < 1e-15:
        return False
    elif i == 1: # Deform if it is the first iteration
        self.simulations[current_simulation].mesh_updated = True
        return True
    else:
        simulation = 'simulation' + str(i-1)
        x_old = self.simulations[simulation].design_vars
        if len(x) is not len(x_old):
            print 'ERROR: Design variables are not the same length'
            sys.exit()
        if np.array_equal(x,x_old):
            return False
        else:
            self.simulations[current_simulation].mesh_updated = True
            return True
