"""This module allows to run SU2 from Dakota.

Run using SU2Dakota.run(config,eval_id,asv,x,u)

This module makes use of the SU2 module.
""" 

import os, shutil
import json
import re
import numpy as np
from SU2.util.bunch import Bunch
from record import Record

import sys

import SU2

def run(record_name,config,eval_id,asv,x=[],u={}):
  """Run SU2. Return values specified in asv.

  Args:
    record_name (str): Filename of the record of simulations. JSON file.
    config (config): A SU2 config class.
    eval_id (int): The evaluation number.
    asv ([int]): The active set vector, indicates desired simulator outputs.
      For more information see Active Set Vector subsection in
      Dakota user's manual.
    x ([float]): design vector.
    u ({}): uncertain variables. The KEY has to be a valid SU2 
      configuration option {'MACH_NUMBER': 0.8,...}
  
  Returns:
    returndict ({}): function, gradient, constrain values as specified in asv.
  """
  
  # Create a record to keep track of the simulations
  record_name = '../' + record_name # because running dakota with folders
  if os.path.isfile(record_name):
    print 'Loading record of simulations'
    record = Record(record_name)
  else:
    print 'Creating new record of simulations'
    record = Record()
  
  # Initialize the simulation in the record simulations
  simulation = 'simulation' + str(eval_id)
  record.simulations[simulation] = Bunch()
  record.simulations[simulation].design_vars = x
  record.simulations[simulation].uncertain_vars = u
  record.simulations[simulation].directory = os.path.abspath('.')
  record.nsimulations = eval_id
  
  # Run the simulation
  link_mesh(config) 
  returndict = {} 
   
  if (asv[0] & 1): # function
      f = func(record,config,x,u)
      returndict['fns'] = [f] # return list for now
      record.simulations[simulation].function = f

  if (asv[0] & 2): # gradient function
      g = grad(record,config,x,u)
      returndict['fnGrads'] = [g] # return list for now
      record.simulations[simulation].gradient = g
  
#  if (asv[1] & 1): # constrain
#      f = cons(record,config,x,u)
#      returndict['fns'] = [f] # return list for now
#      record.simulations[simulation].function = f

#  if (asv[1] & 2): # gradient constrain
#      g = cons_grad(record,config,x,u)
#      returndict['fnGrads'] = [g] # return list for now
#      record.simulations[simulation].gradient = g

  # To add another constrain asv[2] and call the right the function.

  
  # Write out the record of simulations
  file = open(record_name,'w')
  #print json.dumps(record,indent=2)
  json.dump(record,file,indent=2)
  file.close()

  return returndict

def update_config(record,config,x,u):
  '''Set up problem with the correct design and uncertain variables.
  
  Modifies the config to have the desired design and uncertain variables
  values. If necessary it will perform a mesh deformation to account
  for the updated design variables.
  '''

  # Check for design problem
  if x:
    # Check if mesh deformation needed for the current design vector.
    if record.deform_needed(x):
      deform_mesh(config,x)
    
  # Check for uq problem
  if u:
    for key in u.keys():
      config[key] = u[key]
      print key
    config.write() # Do I even need to write the config?
  
def func_setup(folder_name,config):
  setup_folder(folder_name)
  link_mesh(config)

def restart2solution(config):
  '''Moves restart file to solution file.'''
  
  if config.MATH_PROBLEM == 'DIRECT':
    restart = config.RESTART_FLOW_FILENAME
    solution = config.SOLUTION_FLOW_FILENAME
    shutil.move(restart,solution)
  elif config.MATH_PROBLEM == 'ADJOINT':
    restart = config.RESTART_ADJ_FILENAME
    solution = config.SOLUTION_ADJ_FILENAME
    # add suffix
    func_name = config.OBJECTIVE_FUNCTION
    suffix = SU2.io.get_adjointSuffix(func_name)
    restart = SU2.io.add_suffix(restart,suffix)
    solution = SU2.io.add_suffix(solution,suffix)
    shutil.move(restart,solution)
  else:
    raise Exception, 'unknown math problem'

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
  
def grad_setup(folder_name,config):
  # Change the folder name here with the cd ending.
  setup_folder(folder_name)
  link_mesh(config)
  # provide the direct solution for the adjoint solver
  #src = '../direct/' + config.RESTART_FLOW_FILENAME
  src = '../direct/' + config.SOLUTION_FLOW_FILENAME
  dst = config.SOLUTION_FLOW_FILENAME
  shutil.copy(src,dst)

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

def projection(config, step=1e-3):
  
  # files out
  objective      = config['OBJECTIVE_FUNCTION']
  grad_filename  = config['GRAD_OBJFUNC_FILENAME']
  output_format  = config['OUTPUT_FORMAT']
  plot_extension = SU2.io.get_extension(output_format)
  adj_suffix     = SU2.io.get_adjointSuffix(objective)
  grad_plotname  = os.path.splitext(grad_filename)[0] + '_' + adj_suffix + plot_extension
  


def deform_mesh(config,x):
  """Make a new mesh corresponding to design vector x."""
  print 'deforming mesh ...'
  config.unpack_dvs(x)
  folder_name = 'deform'
  setup_folder(folder_name)
  # link original (undeformed) mesh
  mesh_filename = config.MESH_FILENAME
  src = '../../' + mesh_filename
  dst = mesh_filename
  os.symlink(src,dst)
  
  log = 'log_Deform.out'
  with SU2.io.redirect_output(log):
    SU2.run.DEF(config)
  
  # move updated mesh to correct location
  mesh_filename = config.MESH_FILENAME
  mesh_filename_deformed = config.MESH_OUT_FILENAME
  src = mesh_filename_deformed
  dst = '../' + mesh_filename
  shutil.move(src,dst)
  # return to the directory this function was called from
  os.chdir('..')
  print 'finished deforming mesh.'

def link_mesh(config):
  '''Links the mesh to the current working directory.'''
  mesh_filename = config.MESH_FILENAME
  src = '../' + mesh_filename
  dst = mesh_filename
  os.symlink(src,dst)

def setup_folder(folder):
  """Make folder and move into it."""
  # check, make folder
  if not os.path.exists(folder):
    os.makedirs(folder)
  # change directory
  os.chdir(folder)

