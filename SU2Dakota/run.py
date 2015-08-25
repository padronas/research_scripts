"""Module for running SU2."""

import SU2
import os

def func(record,config,x,u):
  
  print 'running (the function) direct problem ...'
  
  ### Pre-run ###
  update_config(record,config,x,u) 
  folder_name = 'direct'
  config.MATH_PROBLEM = 'DIRECT'
  func_setup(folder_name,config)
  
  ### Run ###
  log = 'log_Direct.out'
  with SU2.io.redirect_output(log):
    # Run the CFD
    SU2.run.CFD(config)
    # Run the Solution Exporting Code
    restart2solution(config)
    SU2.run.SOL(config)

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
  print 'finished running direct problem.'
  
  return f
  
def grad(record,config,x,u):
  
  print 'running (the gradient) adjoint problem ...'
  
  ### Pre-run ###
  update_config(record,config,x,u)
  folder_name = 'adjoint'
  config.MATH_PROBLEM = 'ADJOINT'
  grad_setup(folder_name,config)

  ### Run ###
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
  
  ### Post-run ###
  # process outputs
  f = open('of_grad.dat','r')
  f.readline()
  g = []
  for line in f:
    g.append(float(line))
  # return to the directory this function was called from
  os.chdir('..')
  print 'finished running the adjoint problem.'
  
  return g




