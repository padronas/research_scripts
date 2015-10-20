"""Module for running SU2."""

import SU2
import os
from .utils import setup, restart2solution, postprocess, check_for_function, check_convergence


def func(record, config, x, u):

    f = check_for_function(record, config)
    if f is not None:
        return f

    ### Pre-run ###
    folder_name = 'direct'
    config.MATH_PROBLEM = 'DIRECT'
    setup(folder_name, record, config)

    ### Run ###
    print 'running (the function) direct problem ...'
    log = 'log_Direct.out'
    with SU2.io.redirect_output(log):
        # Run the CFD
        SU2.run.CFD(config)
        # Run the Solution Exporting Code
        restart2solution(config)
        #SU2.run.SOL(config)
    print 'finished running direct problem.'

    ### Post-run ###
    f = postprocess(record, config)
    check_convergence(record,config,folder_name)

    # return to the directory this function was called from
    os.chdir('..')

    return f


def grad(record, config, x, u):

    ### Pre-run ###
    folder_name = 'adjoint'
    # add suffix to folder
    func_name = config.OBJECTIVE_FUNCTION
    suffix = SU2.io.get_adjointSuffix(func_name)
    folder_name = SU2.io.add_suffix(folder_name, suffix)
    config.MATH_PROBLEM = 'CONTINUOUS_ADJOINT'
    setup(folder_name, record, config)

    ### Run ###
    print 'running (the gradient) ' + folder_name + ' problem ...'
    log = 'log_Adjoint.out'
    with SU2.io.redirect_output(log):
        # Run the CFD
        SU2.run.CFD(config)
        # Run the Solution Exporting Code
        restart2solution(config)
        #SU2.run.SOL(config)
        # Run the Gradient Projection Code
        step = [0.001] * len(x)
        config.unpack_dvs(step)
        SU2.run.DOT(config)
    print 'finished running the ' + folder_name + ' problem.'

    ### Post-run ###
    # process outputs
    f = open('of_grad.dat', 'r')
    f.readline()
    g = []
    for line in f:
        g.append(float(line))
    check_convergence(record,config,folder_name)

    # return to the directory this function was called from
    os.chdir('..')

    return g
