"""Helper utilities."""

import shutil, os

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

def func_setup(folder_name,config):
  setup_folder(folder_name)
  link_mesh(config)

def grad_setup(folder_name,config):
  # Change the folder name here with the cd ending.
  setup_folder(folder_name)
  link_mesh(config)
  # provide the direct solution for the adjoint solver
  #src = '../direct/' + config.RESTART_FLOW_FILENAME
  src = '../direct/' + config.SOLUTION_FLOW_FILENAME
  dst = config.SOLUTION_FLOW_FILENAME
  shutil.copy(src,dst)

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



