
import json
import os
from SU2.util.bunch import *


class Record(Bunch):
    """Starts a new Record class, an extension of Bunch

      use 1: initialize empty
      use 2: initialize by a record file json

    """

    def __init__(self, filename, config):
        if os.path.isfile(filename):
            print 'Loading record of simulations'
            record_file = open(filename, 'r')
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
