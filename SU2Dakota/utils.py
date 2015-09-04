"""Helper utilities."""

import shutil, os
import re
import SU2

def get_previous_dir(i,j=1): 
  """Return previous directory.

  Inputs: i (int) - the current simulation
          j (int) - Specifies part of the directory
  """
  cwd = os.getcwd()
  directory = cwd.split('/')[-j]
  match = re.search('[\w-]+\.',directory)
  base_name = match.group()
  previous_directory = base_name + str(i-1) + '/'
  return previous_directory

def setup_restart(folder_name,record,config):

  iteration = record.nsimulations
  if iteration != 1: # Copy from the previous simulation.
    previous_directory = get_previous_dir(iteration,2)
    previous_directory = previous_directory + folder_name + '/'
    # Make this a function
    if config.MATH_PROBLEM == 'DIRECT':
      solution_filename = config.SOLUTION_FLOW_FILENAME
      src = '../../' + previous_directory + solution_filename
      dst = solution_filename
    elif config.MATH_PROBLEM == 'ADJOINT':
      solution_filename = config.SOLUTION_ADJ_FILENAME
      # add suffix
      func_name = config.OBJECTIVE_FUNCTION
      suffix = SU2.io.get_adjointSuffix(func_name)
      solution_filename = SU2.io.add_suffix(solution_filename,suffix)
      src = '../../' + previous_directory + solution_filename
      dst = solution_filename
    else:
      raise Exception('unkown math problem')
    shutil.copy(src,dst)
    config.RESTART_SOL = 'YES'

def get_mesh(record,config):
  
  mesh_filename = config.MESH_FILENAME
  if os.path.isfile(mesh_filename):
    # Mesh is already in this simulation directory 
    # The mesh deformation in update_config() put it here.
    pass
  else: # Get mesh from the appropriate location
    i = record.nsimulations
    current_simulation = 'simulation' + str(i)
    if i==1:
      link_mesh(config)
    else:
      try:
        if record.simulations[current_simulation].copy_mesh == True:
          #link mesh from previous iteration, for OUU problems.
          mesh_filename = config.MESH_FILENAME
          previous_directory = get_previous_dir(i)
          src = '../' + previous_directory + mesh_filename
          dst = mesh_filename
          #shutil.copy(src,dst)
          try:
            os.symlink(src,dst)
          except OSError, e:
            if e.errno == errno.EEXIST:
              os.remove(dst)
              os.symlink(src,dst)
      except AttributeError:
        link_mesh(config)

def setup(folder_name,record,config):
  setup_folder(folder_name)
  link_mesh(config)
  setup_restart(folder_name,record,config)
  # provide the direct solution for the adjoint solver
  if config.MATH_PROBLEM == 'ADJOINT':
    #src = '../direct/' + config.RESTART_FLOW_FILENAME
    src = '../direct/' + config.SOLUTION_FLOW_FILENAME
    dst = config.SOLUTION_FLOW_FILENAME
    #shutil.copy(src,dst)
    os.symlink(src,dst)
  


def link_mesh(config):
  '''Links the mesh to the current working directory from up a directory.'''
  mesh_filename = config.MESH_FILENAME
  src = '../' + mesh_filename
  dst = mesh_filename
  try:
    os.symlink(src,dst)
  except OSError, e:
    if e.errno == errno.EEXIST:
      os.remove(dst)
      os.symlink(src,dst)

def setup_folder(folder):
  """Make folder and move into it."""
  # check, make folder
  if not os.path.exists(folder):
    os.makedirs(folder)
  # change directory
  os.chdir(folder)

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
    raise Exception('unknown math problem')


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
  
  config.unpack_dvs(x)
  folder_name = 'deform'
  setup_folder(folder_name)
  # link original (undeformed) mesh
  mesh_filename = config.MESH_FILENAME
  src = '../../' + mesh_filename
  dst = mesh_filename
  os.symlink(src,dst)
 
  ### Run ###
  print 'deforming mesh ...'
  log = 'log_Deform.out'
  with SU2.io.redirect_output(log):
    SU2.run.DEF(config)
  print 'finished deforming mesh.'
  
  # move updated mesh to correct location
  mesh_filename = config.MESH_FILENAME
  mesh_filename_deformed = config.MESH_OUT_FILENAME
  src = mesh_filename_deformed
  dst = '../' + mesh_filename
  shutil.move(src,dst)
  # return to the directory this function was called from
  os.chdir('..')



