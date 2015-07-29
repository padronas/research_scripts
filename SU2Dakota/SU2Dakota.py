
import os, shutil
import numpy as np

# This file is in progress.
import SU2
# I should be able to run UQ, Optimization and OUU.
def run(simulation,x=[],u=[]):
  print 'Running SU2... '
  # Need to figure out best way to run process Popen what other things have I used in the past look at Trent's stuff.
  
  # Update config with uncertain variables
  print 'x = ', x
  print 'u = ', u
  
  #if design variable is the same don't do anything 
  # x_old lives in the project.
  # Also if x is new reset the simulations.
  
  
  if not simulation.simulations:
   initialize_folders()
  
  
  # unpack the uncertain variables
  config = simulation.config
  for key in u.keys():
    config[key] = u[key]
    
  config.write()
  
  # if change deform mesh then run either the adjoing and projection for the gradient, or run for the direct solution directly
  
  #SU2.run.CFD(config) # I probably want to call this later on, have it abstracted away.
  print 'Finished running SU2.'
  
  
def initialize_folders():
  folder_name = 'imulation' # Has the tag from the input file Dakota.
  if not os.path.exists(folder_name):
    os.makedirs(folder_name)
    print folder_name
    
def func(record,config,x=[],u={}):
  
  # Check if it is a design problem
  # Make this a function and have it in the gradient as well.
  if x:
    print 'Running design problem'
    config.unpack_dvs(x)
    print x
    config.write()
    # Check we have already deformed
    if not x == x_old:
      pass
      # We would deform the mesh
      # copy(link) the mesh to the right spot
    
  # unpack the uncertain variables
  # Make this a function and have it in the gradient as well.
  # Can call it set uncertain variables.
  if u:
    for key in u.keys():
      config[key] = u[key]
      print key
    config.write() # Do I even need to write the config?
    
  # Check similar files
  # Check restart function.
  # Find nearest simulation
  dist = np.inf
  restart_directory = ''
  for simulation in record.keys():
    distance_vector = []
    for uncertain_var in record[simulation]['uncertain_vars'].keys():
      distance_vector.append(record[simulation]['uncertain_vars'][uncertain_var] - u[uncertain_var])
    distance = np.linalg.norm(distance_vector,1)
    if distance > 1e-15: #ignore if I'm comparing the current(same) simulation
      if distance < dist:
        dist = distance
        restart_directory = record[simulation]['directory']
  
  if restart_directory:
    print dist
    print 'Restart directory'
    print restart_directory
  # Have a function that makes it restart change config to restart and solution file
  if restart_directory:
    config.RESTART_SOL = 'YES'
    src = os.path.join(restart_directory,'restart_flow.dat')
    dest = os.path.join(os.path.abspath('.'),'solution_flow.dat')
    shutil.copy(src,dest)
    print '\n\n I am restarting the solution'
    config.write()
    
    
  
  
  SU2.run.CFD(config)
  # Aqui en record things that I want to keep track off.
  # Read the history file, read some other stuff.
  history = SU2.io.read_history('history.dat') # whatever the config_name of the history file is.
  f = history['LIFT'][-1]
  
  
  return f
  
  
  
def grad(record,config,x=[],u={}):
  return 6
  
  