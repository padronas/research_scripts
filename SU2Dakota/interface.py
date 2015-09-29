"""Module provides interface between SU2 and Dakota"""
import os
import sys
import json
import re
from SU2.util.bunch import Bunch
from .record import Record
from .run import *


def run(record_name, config, eval_id, asv, x=[], u={}):
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
    record_name = '../' + record_name  # because running dakota with folders
    record = Record(record_name,config)

    # Number of simulations in record
    record.nsimulations = eval_id
    # Initialize the simulation in the record simulations
    simulation = 'simulation' + str(eval_id)
    record.simulations[simulation] = Bunch()
    record.simulations[simulation].design_vars = x
    record.simulations[simulation].uncertain_vars = u
    record.simulations[simulation].directory = os.path.abspath('.')
    record.simulations[simulation].mesh_updated = False

    # Run the simulation
    returndict = {}

    if (asv[0] & 1):  # function
        f = func(record, config, x, u)
        returndict['fns'] = [f]  # return list for now
        record.simulations[simulation].function = f

    if (asv[0] & 2):  # gradient function
        g = grad(record, config, x, u)
        returndict['fnGrads'] = [g]  # return list for now
        record.simulations[simulation].gradient = g

    # Can have this in a try statement if it is an unconstrained problem.
    # if (asv[1] & 1): # constrain
    # print 'Aloha'
    # sys.exit()
    # pass
    #      f = cons(record,config,x,u)
    #      returndict['fns'] = [f] # return list for now
    #      record.simulations[simulation].function = f

#  if (asv[1] & 2): # gradient constrain
#      g = cons_grad(record,config,x,u)
#      returndict['fnGrads'] = [g] # return list for now
#      record.simulations[simulation].gradient = g

    # To add another constrain asv[2] and call the right the function.

    # Write out the record of simulations
    file = open(record_name, 'w')
    # print json.dumps(record, indent=2)
    json.dump(record, file, indent=2)
    file.close()

    return returndict

def parse_dakota_parameters_file(paramsfilename):
    """Return parameters for application."""

    # setup regular expressions for parameter/label matching
    e = r'-?(?:\d+\.?\d*|\.\d+)[eEdD](?:\+|-)?\d+'  # exponential notation
    f = r'-?\d+\.\d*|-?\.\d+'                       # floating point
    i = r'-?\d+'                                    # integer
    value = e + '|' + f + '|' + i                           # numeric field
    tag = r'\w+(?::\w+)*'                           # text tag field

    # regular expression for standard parameters format
    standard_regex = re.compile('^\s*(' + value + ')\s+(' + tag + ')$')

    # open DAKOTA parameters file for reading
    paramsfile = open(paramsfilename, 'r')

    # extract the parameters from the file and store in a dictionary
    paramsdict = {}
    for line in paramsfile:
        m = standard_regex.match(line)
        if m:
            # print m.group()
            paramsdict[m.group(2)] = m.group(1)

    paramsfile.close()

    return paramsdict


def write_dakota_results_file(
        resultfilename, resultsdict, paramsdict, active_set_vector):
    """Write results of application for Dakota."""

# Make sure number of functions is as expected.
    num_fns = 0
    if ('functions' in paramsdict):
        num_fns = int(paramsdict['functions'])
    if num_fns != len(resultsdict['fns']):
        raise Exception('Number of functions not as expected.')

    # write outputfile
    outfile = open(resultfilename, 'w')

    for func_ind in range(0, num_fns):
        # write functions
        if (active_set_vector[func_ind] & 1):
            functions = resultsdict['fns']
            outfile.write(str(functions[func_ind]) +
                          ' f' + str(func_ind) + '\n')

    # write gradients
    for func_ind in range(0, num_fns):
        if (active_set_vector[func_ind] & 2):
            grad = resultsdict['fnGrads'][func_ind]
            outfile.write('[ ')
            for deriv in grad:
                outfile.write(str(deriv) + ' ')
            outfile.write(']\n')

    outfile.close()


def check_dakota_input(file):
    """Verify if dakota input file is set up correctly for SU2Dakota."""

    try:  # This try statement should execute if running with directories.
        file1 = '../' + file
        f = open(file1, 'r')
        f.close()
    except IOError: #Tell people to activate running with directories.
        good = False
        f = open(file,'r')
        for line in f:
            if 'work_directory' in line:
                if line.split()[0][0] != '#':
                    good = True
        f.close()
        if not good:
            message1 = 'Error: Need dakota keyword work_directory in ' + f.name +'\n'
            message2 = '''Also include:
                    named = 'workdir'
                    directory_tag
                    directory_save
                  and optionally:
                    parameters_file = 'params.in'
                    results_file = 'results.out'
                    file_tag
                    file_save'''
            message = message1 + message2
            sys.exit(message)
