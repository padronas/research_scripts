#!/usr/bin/env python

# Read DAKOTA parameters file standard format and call SU2
# python module for analysis and return the results file to Dakota.

# DAKOTA will execute this script as
#   SU2_dakota_interface.py params.in results.out
#   so sys.argv[1] will be the parameters file and
#   sys.argv[2] will be the results file to return to DAKOTA

# necessary python modules
import sys
import re
import os
import SU2

def main():
  
  # ----------------------------
  # Parse DAKOTA parameters file
  # ----------------------------
  paramsfile = sys.argv[1]
  paramsdict = parse_dakota_parameters_file(paramsfile)

  # ----------------------
  # Setting up application
  # ----------------------
  
  # -------------------------------
  # Convert and send to application
  # -------------------------------

  ########## Modify here for your problem ##########
  
  ### Config file options ### 
  config_filename = 'inv_NACA0012_opt.cfg'
  # Create a config container
  config_filename = '../' + config_filename # Because running dakota with folders
  config = SU2.io.Config(config_filename)
  # Number of processors to run simulation on
  config.NUMBER_PART = 16
  
  # Optimization objective
  #config.OPT_OBJECTIVE = 'DRAG' Maybe have this in the config file itself
  
  ### Dictionary for passing to your application (SU2) ### 
  SU2_params = {}
  SU2_params['config'] = config
  SU2_params['uncertain_vars'] = {} # populate this below, problem specific
  SU2_params['design_vars'] = [] # populate this below, problem specific
  SU2_params['eval_id'] = int(paramsdict['eval_id'])
  
  ### Modify the paramsdict names to match those of the params file ###
  
  # For information of the active set vector see
  # The Active Set Vector subsection of the Dakota user's manual
  active_set_vector = [ int(paramsdict['ASV_1:obj_fn']) ]
  SU2_params['asv'] = active_set_vector
  
  # Specify uncertain variables, uncomment and modify as needed.
  nu_var = 0
  # the KEY has to be a valid SU2 configuration option
  # SU2_params['uncertain_vars'][KEY] = ...
  # SU2_params['uncertain_vars']['MACH_NUMBER'] = float(paramsdict['Mach'])
  
  # Specify design variables, uncomment and modify as needed.
  nd_var = 38
  for i in range(1,nd_var+1):
    var = 'x' + str(i)
    SU2_params['design_vars'].append(float(paramsdict[var]))
  
  print SU2_params['design_vars']
  print len(SU2_params['design_vars'])
  #SU2_params['functions'] = ['LIFT']
  
  # rough error checking
  nvar = nd_var + nu_var
  num_vars = 0
  if ('variables' in paramsdict):
      num_vars = int(paramsdict['variables'])
  if (num_vars != nvar):
    print 'ERROR: Simulation expected ' + str(nvar) + ' variables, found ' \
                                    + str(num_vars) + ' variables.'
    sys.exit()
  
  # This is used for the output, not sure if I'll use it here,
  # otherwise I can push it to the output section
  num_fns = 0
  if ('functions' in paramsdict):
      num_fns = int(paramsdict['functions'])
  SU2_params['nfunctions'] = num_fns
  

  # execute the SU2 analysis
  import SU2Dakota
  print "Running SU2..."
  resultsdict = SU2Dakota.run(**SU2_params)
  print "SU2 complete."
  print resultsdict

  




  # ----------------------------
  # Return the results to DAKOTA
  # ----------------------------

  # write the results.out file for return to DAKOTA
  # this example only has a single function, so make some assumptions;
  # not processing DVV
  outfile = open('results.out.tmp', 'w')

  # write functions
  for func_ind in range(0, num_fns):
      if (active_set_vector[func_ind] & 1):
          functions = resultsdict['fns']
          outfile.write(str(functions[func_ind]) + ' f' + str(func_ind) + '\n')

  # write gradients
  for func_ind in range(0, num_fns):
    if (active_set_vector[func_ind] & 2):
      grad = resultsdict['fnGrads'][func_ind]
      outfile.write('[ ')
      for deriv in grad:
        outfile.write(str(deriv) + ' ')
      outfile.write(']\n') 
  
  outfile.close()

  # move the temporary results file to the one DAKOTA expects
  import shutil
  shutil.move('results.out.tmp', sys.argv[2])
  #os.system('mv results.out.tmp ' + sys.argv[2])
  

def parse_dakota_parameters_file(paramsfilename):
  '''Return parameters for application.'''
  
  # setup regular expressions for parameter/label matching
  e = r'-?(?:\d+\.?\d*|\.\d+)[eEdD](?:\+|-)?\d+'  # exponential notation
  f = r'-?\d+\.\d*|-?\.\d+'                       # floating point
  i = r'-?\d+'                                    # integer
  value = e+'|'+f+'|'+i                           # numeric field
  tag = r'\w+(?::\w+)*'                           # text tag field

  # regular expression for standard parameters format
  standard_regex = re.compile('^\s*('+value+')\s+('+tag+')$')

  # open DAKOTA parameters file for reading
  paramsfile = open(paramsfilename, 'r')

  # extract the parameters from the file and store in a dictionary
  paramsdict = {}
  for line in paramsfile:
      m = standard_regex.match(line)
      if m:
          #print m.group()
          paramsdict[m.group(2)] = m.group(1)

  paramsfile.close()
  
  return paramsdict
  



if __name__ == '__main__':
  main()
