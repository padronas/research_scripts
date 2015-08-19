
import os, shutil
import json
import re
import numpy as np
from SU2.util.bunch import Bunch
from record import Record

import sys

# This file is in progress.
import SU2
# I should be able to run UQ, Optimization and OUU.

def copy_mesh(config,i):
  '''Copies the mesh to the current working directory.'''
  
  mesh_filename = config.MESH_FILENAME
  
  if i==1: # First iteration copy from the directory we started Dakota.
    src = '../' + mesh_filename
    dst = mesh_filename
  else: # Copy from the previous simulation.
    cwd = os.getcwd()
    directory = cwd.split('/')[-1]
    match = re.search('[\w-]+\.',directory)
    base_name = match.group()
    previous_directory = base_name + str(i-1) + '/'
    src = '../' + previous_directory + mesh_filename
    dst = mesh_filename
  shutil.copy(src,dst)

def link_mesh(config):
  '''Links the mesh to the current working directory.'''

  mesh_filename = config.MESH_FILENAME
  src = '../' + mesh_filename
  #base, ext = os.path.splitext(mesh_filename)
  #dst = base + '_original' + ext
  dst = mesh_filename
  os.symlink(src,dst)
  #config.MESH_FILENAME = dst

def run(**SU2_params):
  '''Runs the problem '''
  
  x = SU2_params['design_vars'] # design vector
  u = SU2_params['uncertain_vars']
  asv = SU2_params['asv'] # Active set vector, indicates which simulator outputs are needed.
  config = SU2_params['config']
  i = SU2_params['eval_id']

  #copy_mesh(config,i)
  link_mesh(config) 
    
  # Create a record to keep track of the simulations
  #record_name = 'record.json'
  record_name = '../record.json' # because running with folders do similar to config
  if os.path.isfile(record_name):
    print 'Loading record of simulations'
    record = Record(record_name)
  else:
    print 'Creating new record of simulations'
    record = Record()
  simulation = 'simulation' + str(i)
  # Start populating the simulation in the record simulations
  record.simulations[simulation] = Bunch()
  record.simulations[simulation].design_vars = x
  record.simulations[simulation].uncertain_vars = u
  record.nsimulations = i
  
  returndict = {} 
   
  if (asv[0] & 1): # **** f:
      f = func(record,config,x,u)
      #f = SU2.opt.scipy_tools.obj_f(x,project)
      returndict['fns'] = [f] # return list for now
      record.simulations[simulation].function = f

  if (asv[0] & 2): # **** df/dx:
      g = grad(record,config,x,u)
      #g = SU2.opt.scipy_tools.obj_df(x,project)
      # Will need to get this in the list form
      #g = [ [-400*f0*x[0] - 2*f1, 200*f0] ]
      #returndict['fnGrads'] = [g.tolist()] # return list for now
      returndict['fnGrads'] = [g] # return list for now

  # Populate record
  record.simulations[simulation].directory = os.path.abspath('.')

  # Write out the record
  file = open(record_name,'w')
  print json.dumps(record, indent=2)
  json.dump(record,file, indent=2)
  file.close()
  

  return returndict
  
  # # Need to figure out best way to run process Popen what other things have I used in the past look at Trent's stuff.
  #
  # # Update config with uncertain variables
  # print 'x = ', x
  # print 'u = ', u
  #
  # #if design variable is the same don't do anything
  # # x_old lives in the project.
  # # Also if x is new reset the simulations.
  #
  #
  # if not simulation.simulations:
  #  initialize_folders()
  
  
def initialize_folders():
  folder_name = 'imulation' # Has the tag from the input file Dakota.
  if not os.path.exists(folder_name):
    os.makedirs(folder_name)
    print folder_name

def deform_mesh(config,x):
  
  config.unpack_dvs(x)
  folder_name = 'deform'
  make_folder(folder_name,config)
  #link_mesh(config)
  # link_mesh from 2 levels back, prevents overwritting
  mesh_filename = config.MESH_FILENAME
  src = '../../' + mesh_filename
  #base, ext = os.path.splitext(mesh_filename)
  #dst = base + '_original' + ext
  dst = mesh_filename
  os.symlink(src,dst)
  
#base, ext = os.path.splitext(mesh_filename)
  #dst = base + '_original' + ext
  log = 'log_Deform.out'
  with SU2.io.redirect_output(log):
    SU2.run.DEF(config)
  mesh_filename = config.MESH_FILENAME
  mesh_filename_deformed = config.MESH_OUT_FILENAME
  src = mesh_filename_deformed
  #base, ext = os.path.splitext(mesh_filename)
  #dst = '../' + base + '_deformed' + ext
  dst = '../' + mesh_filename
  shutil.move(src,dst)
  os.chdir('..')

def func(record,config,x=[],u={}):
  
  # Check if it is a design problem
  # Make this a function and have it in the gradient as well.
  if x:
    print 'Running design problem'
    # Check we have already deformed
    if record.deform_needed(x):
      deform_mesh(config,x)
    
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
  # dist = np.inf
  # restart_directory = ''
  # for simulation in record.simulations.keys():
  #   print '\n\n making some room'
  #   print record.simulations.keys()
  #   print simulation
  #   print record.simulations[simulation]
  #   distance_vector = []
  #   for uncertain_var in record.simulations[simulation].uncertain_vars.keys():
  #     distance_vector.append(record.simulations.simulation.uncertain_vars.uncertain_var - u[uncertain_var])
  #   distance = np.linalg.norm(distance_vector,1)
  #   if distance > 1e-15: #ignore if I'm comparing the current(same) simulation
  #     if distance < dist:
  #       dist = distance
  #       restart_directory = record.simulations.simulation.directory
  #
  # if restart_directory:
  #   print dist
  #   print 'Restart directory'
  #   print restart_directory
  # # Have a function that makes it restart change config to restart and solution file
  # if restart_directory:
  #   config.RESTART_SOL = 'YES'
  #   src = os.path.join(restart_directory,'restart_flow.dat')
  #   dest = os.path.join(os.path.abspath('.'),'solution_flow.dat')
  #   shutil.copy(src,dest)
  #   print '\n\n I am restarting the solution'
  #   config.write()
    
    
  
  #prerun Move files around and stuff
  folder_name = 'direct'
  config.MATH_PROBLEM = 'DIRECT'
  make_folder(folder_name,config)
  link_mesh(config)
  log = 'log_Direct.out'
  with SU2.io.redirect_output(log):
    SU2.run.CFD(config)
  # Aqui en record things that I want to keep track off.
  # Read the history file, read some other stuff.
  history = SU2.io.read_history('history.dat') # whatever the config_name of the history file is.
  f = history['DRAG'][-1]
  
  # return to the directory this function was called from
  os.chdir('..')
  
  return f
  
def make_folder(folder,config):
  # check, make folder
  if not os.path.exists(folder):
    os.makedirs(folder)
  # change directory
  os.chdir(folder)
#  # link the mesh file to the directory
#  mesh_filename = config.MESH_FILENAME
#  src = '../' + mesh_filename
#  dst = mesh_filename
#  os.symlink(src,dst)
  
def grad(record,config,x=[],u={}):
  # Check if it is a design problem
  # Make this a function and have it in the gradient as well.
  if x:
    print 'the gradient'
    # Check we have already deformed
    if record.deform_needed(x):
      deform_mesh(config,x)
    
  # unpack the uncertain variables
  # Make this a function and have it in the gradient as well.
  # Can call it set uncertain variables.
  if u:
    for key in u.keys():
      config[key] = u[key]
      print key
    config.write() # Do I even need to write the config?
  
  #prerun Move files around and stuff
  folder_name = 'adjoint'
  config.MATH_PROBLEM = 'ADJOINT'
  make_folder(folder_name,config)
  link_mesh(config)

  src = '../direct/' + config.RESTART_FLOW_FILENAME
  dst = config.SOLUTION_FLOW_FILENAME
  shutil.copy(src,dst)
  log = 'log_Adjoint.out'
  with SU2.io.redirect_output(log):
    SU2.run.CFD(config)
# Doing the unpack here with the step size, I can keep my original logic of when to deform. But still modify to include the already deform part.
  step = [0.001]*len(x)
  config.unpack_dvs(step)
  log = 'log_GradientProjection.out'
  with SU2.io.redirect_output(log):
    SU2.run.DOT(config)
  
  f = open('of_grad.dat','r')
  f.readline()
  g = []
  for line in f:
    g.append(float(line))
  # return to the directory this function was called from
  os.chdir('..')
  
  return g
  
  
