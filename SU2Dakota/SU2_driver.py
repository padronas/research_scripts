import os
import json
from SU2Dakota import func
from SU2Dakota import grad

def SU2_run(**SU2_params):
  '''Runs the problem '''
    
  x = SU2_params['design_vars'] # design vector
  u = SU2_params['uncertain_vars']
  asv = SU2_params['asv'] # Active set vector, indicates which simulator outputs are needed.
  config = SU2_params['config']


  # Create a record to keep track of the simulations
  record_name = 'record.json'
  if os.path.isfile(record_name):
    print 'loading record of simulations'
    record_file = open(record_name,'r')
    record = json.load(record_file)
    record_file.close()
  else:
    print 'creating new record of simulations'
    record = {}
  simulation = 'simulation' + str(SU2_params['eval_id'])
  # Start populatibg the record of this simulation
  record[simulation] = {'design_vars': x,'uncertain_vars': u}
  
  returndict = {} 
   
  if (asv[0] & 1): # **** f:
      f = func(record,config,x,u)
      #f = SU2.opt.scipy_tools.obj_f(x,project)
      returndict['fns'] = [f] # return list for now
      record[simulation]['func'] = f

  if (asv[0] & 2): # **** df/dx:
      g = grad(record,config,x,u)
      #g = SU2.opt.scipy_tools.obj_df(x,project)
      # Will need to get this in the list form
      #g = [ [-400*f0*x[0] - 2*f1, 200*f0] ]
      #returndict['fnGrads'] = [g.tolist()] # return list for now
      returndict['fnGrads'] = [g] # return list for now

  # Populate record
  record[simulation]['directory'] = os.path.abspath('.')

  # Write out the record
  file = open(record_name,'w')
  print json.dumps(record, indent=2)
  json.dump(record,file, indent=2)
  file.close()
  

  return returndict
  #
  #   import os
  #   import SU2
  #
  #   # Config file name and number of processors specified here.
  #   config_filename = 'inv_NACA0012_basic.cfg'
  #   nproc = 16
  #
  #   projectname = 'project.pkl'
  #
  #   config = SU2.io.Config(config_filename)
  #   config.NUMBER_PART = nproc
  #   config.GRADIENT_METHOD = 'ADJOINT'
  #
  #   # State
  #   state = SU2.io.State()
  #   state.find_files(config)
  #
  #   # Project
  #   if os.path.exists(projectname):
  #       project = SU2.io.load_data(projectname)
  #       project.config = config
  #   else:
  #       project = SU2.opt.Project(config,state)
 
    

