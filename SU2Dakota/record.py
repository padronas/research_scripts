
import json
import numpy as np
from SU2.util.bunch import *


class Record(Bunch):
  """Starts a new Record class, an extension of Bunch
  
    use 1: initialize empty
    use 2: initialize by a record file json
  
  """
  
  def __init__(self, filename=''):
    if filename:
      record_file = open(filename,'r')
      record_dict = json.load(record_file)
      #self.simulations = bunchify(record_dict['simulations'])
      self.update(bunchify(record_dict))
      record_file.close()
    else:
      self.simulations = Bunch()

  def deform_needed(self,x):
    '''Checks if deformation needed.'''
    
    i = self.nsimulations
    current_simulation = 'simulation' + str(i)
    
    # Don't deform, if I already deformed for the current simulation.
    try:
      if self.simulations[current_simulation].deformed == True:
        print '\n estoy aqui'
        return False
    except AttributeError:
      pass
   
    # Don't deform, if design vector is zero or same as previous simulation.
    if np.linalg.norm(x) < 1e-15:
      return False
    elif i == 1: # Deform if it is the first iteration
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
        self.simulations[current_simulation].deformed = True
        return True
      
      

  
  


