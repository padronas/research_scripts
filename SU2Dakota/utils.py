"""Helper utilities."""

import shutil
import os
import re
import numpy as np
import pandas as pd
import SU2

def get_previous_dir(i, j=1):
    """Return previous directory.

    Inputs: i (int) - the current simulation
            j (int) - Specifies part of the directory
    """
    cwd = os.getcwd()
    directory = cwd.split('/')[-j]
    match = re.search('[\w-]+\.', directory)
    base_name = match.group()
    previous_directory = base_name + str(i - 1) + '/'
    return previous_directory


def setup_restart(folder_name, record, config):

    iteration = record.nsimulations
    if iteration != 1:  # Copy from the previous simulation.
        previous_directory = get_previous_dir(iteration, 2)
        previous_directory = previous_directory + folder_name + '/'
        # Make this a function
        if config.MATH_PROBLEM == 'DIRECT':
            solution_filename = config.SOLUTION_FLOW_FILENAME
            src = '../../' + previous_directory + solution_filename
            dst = solution_filename
        elif config.MATH_PROBLEM == 'CONTINUOUS_ADJOINT':
            solution_filename = config.SOLUTION_ADJ_FILENAME
            # add suffix
            func_name = config.OBJECTIVE_FUNCTION
            suffix = SU2.io.get_adjointSuffix(func_name)
            solution_filename = SU2.io.add_suffix(solution_filename, suffix)
            src = '../../' + previous_directory + solution_filename
            dst = solution_filename
        else:
            raise Exception('unkown math problem')
        shutil.copy(src, dst)
        config.RESTART_SOL = 'YES'


def setup(folder_name, record, config):
    setup_folder(folder_name)
    link_mesh(record, config)
    #setup_restart(folder_name, record, config)
    # provide the direct solution for the adjoint solver
    if config.MATH_PROBLEM == 'CONTINUOUS_ADJOINT':
        #src = '../direct/' + config.RESTART_FLOW_FILENAME
        src = '../direct/' + config.SOLUTION_FLOW_FILENAME
        dst = config.SOLUTION_FLOW_FILENAME
        os.symlink(src, dst)


def link_mesh(record, config):
    '''Links the mesh to the current working directory from up a directory.'''
    mesh_filename = config.MESH_FILENAME
    src = record.current_mesh
    dst = mesh_filename
    os.symlink(src, dst)


def setup_folder(folder):
    """Make folder and move into it."""
    # check, make folder
    if not os.path.exists(folder):
        os.makedirs(folder)
    # change directory
    os.chdir(folder)


def restart2solution(config):
    '''Moves restart file to solution file.'''

    if config.MATH_PROBLEM == 'DIRECT':
        restart = config.RESTART_FLOW_FILENAME
        solution = config.SOLUTION_FLOW_FILENAME
        shutil.move(restart, solution)
    elif config.MATH_PROBLEM == 'CONTINUOUS_ADJOINT':
        restart = config.RESTART_ADJ_FILENAME
        solution = config.SOLUTION_ADJ_FILENAME
        # add suffix
        func_name = config.OBJECTIVE_FUNCTION
        suffix = SU2.io.get_adjointSuffix(func_name)
        restart = SU2.io.add_suffix(restart, suffix)
        solution = SU2.io.add_suffix(solution, suffix)
        shutil.move(restart, solution)
    else:
        raise Exception('unknown math problem')


def deform_needed(record, x):
    """Return bool specifying if mesh deformation needed."""

    i = record.nsimulations
    current_simulation = 'simulation' + str(i)
    if i == 1:
        record.old_design_vector = x

    # Don't deform, if design vector is zero or same as previous simulation.
    if np.linalg.norm(x) < 1e-15:
        return False
    if x == record.old_design_vector:
        return False

    return True


def deform_mesh(record, config, x):
    """Make a new mesh corresponding to design vector x."""

    config.unpack_dvs(x)
    folder_name = 'deform'
    setup_folder(folder_name)

    # link original (undeformed) mesh
    mesh_filename = config.MESH_FILENAME
    src = record.baseline_mesh
    dst = mesh_filename
    os.symlink(src, dst)

    ### Run ###
    print 'deforming mesh ...'
    log = 'log_Deform.out'
    with SU2.io.redirect_output(log):
        SU2.run.DEF(config)
    print 'finished deforming mesh.'

    # updated the current mesh
    mesh_filename_deformed = config.MESH_OUT_FILENAME
    src = mesh_filename_deformed
    dst = mesh_filename
    shutil.move(src, dst)
    record.current_mesh = os.getcwd() + '/' + mesh_filename
    record.old_design_vector = x

    # return to the directory this function was called from
    os.chdir('..')


def postprocess(record, config):
    """Record history and return the quantity of interest."""

    # Read history file, the ending assumes we are running with Tecplot output
    history_filename = config.CONV_FILENAME + '.dat'
    history = SU2.io.read_history(history_filename)
    hist = {}
    kys = ['DRAG', 'LIFT', 'MOMENT_Z']  # Keys we wish to keep.
    for key in history.keys():
        if key in kys:
            hist[key] = history[key][-1]
    simulation = get_current_simulation(record)
    # record the history of the current simulation
    record.simulations[simulation].history = hist
    # The quantity of interest the objective or constrain
    f = hist[config.OBJECTIVE_FUNCTION]

    # Optionally also record the airfoil coordinates
    surface_filename = config.SURFACE_FLOW_FILENAME + '.csv'
    df = pd.read_csv(surface_filename, skipinitialspace=True)
    df = df.sort_index(by='Global_Index')
    x = df.x_coord.tolist()
    y = df.y_coord.tolist()
    coords = {'x': x, 'y': y}
    record.simulations[simulation].airfoil_coordinates = coords

    return f


def postprocess_gradient(filename):
    g = np.squeeze(pd.read_csv(filename).values)
    return g.tolist()


def check_for_function(record, config):
    """Return value if already computed"""

    # If you ran the direct problem you should also have the constrain value.
    simulation = get_current_simulation(record)
    try:
        hist = record.simulations[simulation].history
        f = hist[config.OBJECTIVE_FUNCTION]
    except AttributeError:
        f = None
    return f


def check_convergence(record, config, folder_name):
    """Record in json file the convergence"""

    # Read history file, the ending assumes we are running with Tecplot output
    history_filename = config.CONV_FILENAME + '.dat'
    history = SU2.io.read_history(history_filename)

    simulation = get_current_simulation(record)

    # Rough check to see if solution is converged
    if config.EXT_ITER == len(history['ITERATION']):
        record.simulations[simulation].converged[folder_name] = False
    else:
        record.simulations[simulation].converged[folder_name] = True

def get_current_simulation(record):
    """Return the current simulation (string)"""
    i = record.nsimulations
    return 'simulation' + str(i)
