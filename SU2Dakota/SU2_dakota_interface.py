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

    # -----------------------
    # Check DAKOTA input file
    # -----------------------
    ########## Modify file name for your problem  ##########
    dakota_input_file = 'dakota_NACA0012_opt.in'
    interface.check_dakota_input(dakota_input_file)

    # ----------------------------
    # Parse DAKOTA parameters file
    # ----------------------------
    paramsfile = sys.argv[1]
    paramsdict = interface.parse_dakota_parameters_file(paramsfile)

    # ------------------------
    # Set up application (SU2)
    # ------------------------

    ########## Modify here for your problem ##########

    record_name = 'record.json'  # Keeps track of the simulations
    config_filename = 'inv_NACA0012_opt.cfg'  # SU2 config
    config_filename = '../' + config_filename  # Because running dakota with folders
    config = SU2.io.Config(config_filename)
    config.NUMBER_PART = 16  # Number of processors to run simulation

    # Specify uncertain variables
    nu_var = 1
    uncertain_vars = {}
    # the KEY has to be a valid SU2 configuration option
    uncertain_vars['MACH_NUMBER'] = float(paramsdict['Mach'])

    # Specify number of design variables
    #nd_var = 38
    #design_vars = []
    # for i in range(1,nd_var+1):
    #  var = 'x' + str(i)
    #  design_vars.append(float(paramsdict[var]))

    # Optimization objective
    # config.OPT_OBJECTIVE = 'DRAG' Maybe have this in the config file itself

    ### Dictionary for passing to your application (SU2) ###
    eval_id = int(paramsdict['eval_id'])
    active_set_vector_func = int(paramsdict['ASV_1:Cd'])
    #active_set_vector_func = int(paramsdict['ASV_1:obj_fn'])
    #active_set_vector_cons = int(paramsdict['ASV_2:nln_ineq_con_1'])
    active_set_vector = [active_set_vector_func]
    #active_set_vector = [active_set_vector_func,active_set_vector_cons]

    ### Modify the paramsdict names to match those of the params file ###

    # rough error checking
    try:
        nu_var
    except NameError:
        nu_var = 0
        uncertain_vars = {}
    try:
        nd_var
    except NameError:
        nd_var = 0
        design_vars = []

    nvar = nd_var + nu_var
    num_vars = 0
    if ('variables' in paramsdict):
        num_vars = int(paramsdict['variables'])
    if (num_vars != nvar):
        print 'Error: Simulation expected ' + str(nvar) + ' variables, found ' \
            + str(num_vars) + ' variables.'
        sys.exit()

    # -----------------------------
    # Execute the application (SU2)
    # -----------------------------

    print "Running SU2..."
    resultsdict = interface.run(record_name, config,
                                eval_id, active_set_vector, design_vars, uncertain_vars)
    print "SU2 complete."

    # ----------------------------
    # Return the results to DAKOTA
    # ----------------------------

    resultsfile = sys.argv[2]
    interface.write_dakota_results_file(
        resultsfile, resultsdict, paramsdict, active_set_vector)

if __name__ == '__main__':
    main()
