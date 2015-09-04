"""Module for running SU2."""

import SU2
import os
from .utils import update_config, setup, restart2solution, get_mesh

def func(record,config,x,u):
  
  ### Pre-run ###
  update_config(record,config,x,u) 
  get_mesh(record,config)
  folder_name = 'direct'
  config.MATH_PROBLEM = 'DIRECT'
  setup(folder_name,record,config)
  
  ### Run ###
  print 'running (the function) direct problem ...'
  log = 'log_Direct.out'
  with SU2.io.redirect_output(log):
    # Run the CFD
    SU2.run.CFD(config)
    # Run the Solution Exporting Code
    restart2solution(config)
    SU2.run.SOL(config)
  print 'finished running direct problem.'

  ### Post-run ###
  # process outputs
  # Aqui en record things that I want to keep track off.
  # Read the history file, read some other stuff.
  history_filename = config.CONV_FILENAME + '.dat' 
  # The ending assumes we are running with Tecplot output
  history = SU2.io.read_history(history_filename)
  f = history['DRAG'][-1]
  
  # return to the directory this function was called from
  os.chdir('..')
  
  return f
  
def grad(record,config,x,u):
  
  ### Pre-run ###
  update_config(record,config,x,u)
  get_mesh(record,config)
  folder_name = 'adjoint'
  config.MATH_PROBLEM = 'ADJOINT'
  setup(folder_name,record,config)

  ### Run ###
  print 'running (the gradient) adjoint problem ...'
  log = 'log_Adjoint.out'
  with SU2.io.redirect_output(log):
    # Run the CFD
    SU2.run.CFD(config)
    # Run the Solution Exporting Code
    restart2solution(config)
    SU2.run.SOL(config)
    # Run the Gradient Projection Code
    step = [0.001]*len(x)
    config.unpack_dvs(step)
    SU2.run.DOT(config)
  print 'finished running the adjoint problem.'
  
  ### Post-run ###
  # process outputs
  f = open('of_grad.dat','r')
  f.readline()
  g = []
  for line in f:
    g.append(float(line))
  # return to the directory this function was called from
  os.chdir('..')
  
  return g




