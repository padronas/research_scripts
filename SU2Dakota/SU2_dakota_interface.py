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
import SU2Dakota.interface as interface

def main():
  
  # ----------------------------
  # Parse DAKOTA parameters file
  # ----------------------------
  paramsfile = sys.argv[1]
  paramsdict = interface.parse_dakota_parameters_file(paramsfile)

  # ----------------------
  # Setting up application
  # ----------------------
  
  ########## Modify here for your problem ##########
  
  record_name = 'record.json'
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
  eval_id = int(paramsdict['eval_id'])
  active_set_vector = [ int(paramsdict['ASV_1:obj_fn']) ]
  active_set_vector.append(int(paramsdict['ASV_2:nln_ineq_con_1']) ) # maybe you don't have the one
  
  ### Modify the paramsdict names to match those of the params file ###
  
  # For information of the active set vector see
  # The Active Set Vector subsection of the Dakota user's manual
  
  # Specify uncertain variables
  nu_var = 0
  uncertain_vars = {}
  # the KEY has to be a valid SU2 configuration option
  # uncertain_vars[KEY] = ...
  # uncertain_vars['MACH_NUMBER'] = float(paramsdict['Mach'])
  
  # Specify design variables
  nd_var = 38
  design_vars = []
  for i in range(1,nd_var+1):
    var = 'x' + str(i)
    design_vars.append(float(paramsdict[var]))
  
  
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
  

  # execute the SU2 analysis
  import SU2Dakota
  print "Running SU2..."
  resultsdict = interface.run(record_name,config,
                eval_id,active_set_vector,design_vars,uncertain_vars)
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
  


  



if __name__ == '__main__':
  main()
