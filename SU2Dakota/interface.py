"""Module provides interface between SU2 and Dakota"""
import os
import json
import re
from SU2.util.bunch import Bunch
from record import Record
from .utils import link_mesh
from .run import *

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





