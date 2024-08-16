import subprocess
import pandas as pd
import argparse
import os
import re
from os.path import join
from benchmark import ensure_csv
from benchmark import open_tuple_file
from benchmark import column_names

class TestValueError(Exception):
    """Custom exception for specific errors."""
    def __init__(self, message="Value not found"):
        self.message = message
        super().__init__(self.message)

# Extracts the results of the lamps test into a dictionary
def lammps_results(test_number_directory, test_number, nodes, tasks):
    
    test_file_name = join(test_number_directory, f"lammps_n{nodes}_t{tasks}.out")
    control_test_file_name = join(test_number_directory, "lammps_n1_t1.out")

    if not os.path.exists(test_file_name):
        raise FileNotFoundError(f"The file {test_file_name} does not exist.")

    if not os.path.exists(control_test_file_name):
        raise FileNotFoundError(f"The file {control_test_file_name} does not exist.")

    control_wall_time = None
    wall_time = None
    control_comm_pct = None
    comm_pct = None

    # Extract Loop Time value for the control
    control_lines = open(control_test_file_name,'r').read()
    loop_time_match = re.search(r"Loop time of\s*([\d\.]+)", control_lines)
    if loop_time_match:
        control_wall_time = float(loop_time_match.group(1))

    # Extract Loop Time value
    lines = open(test_file_name,'r').read()
    loop_time_match = re.search(r"Loop time of\s*([\d\.]+)", lines)
    if loop_time_match:
        wall_time = float(loop_time_match.group(1))

    # Extract Percent Time in Communication
    comm_pct_match = re.search(r"Comm\s*\|(?:\s*[\d\.]+\s*\|){4}\s*([\d\.]+)", lines)
    if comm_pct_match:
        comm_pct = float(comm_pct_match.group(1))

    if control_wall_time == None:
        raise TestValueError("No value found for the n1_t1 wall time")
    elif wall_time == None:
        raise TestValueError(f"No value found for the n{nodes}_t{tasks} wall time")
    elif comm_pct == None:
        raise TestValueError("No value found for the n{nodes}_t{tasks} Comm Pct")

    parallel_eff = control_wall_time/wall_time*100
    data = {"Lammps PE": parallel_eff, "Lammps PCTComm": comm_pct}
    return data 

# Extracts the results of the openfoam test into a dictionary
def openfoam_results(test_number_directory, test_number, nodes, tasks):
    
    test_file_name = join(test_number_directory, f"openfoam_n{nodes}_t{tasks}.out")
    test_error_file_name = join(test_number_directory, f"openfoam_n{nodes}_t{tasks}.err")
    control_test_file_name = join(test_number_directory, "openfoam_n1_t1.out")

    if not os.path.exists(test_file_name):
        raise FileNotFoundError(f"The file {test_file_name} does not exist.")

    if not os.path.exists(control_test_file_name):
        raise FileNotFoundError(f"The file {control_test_file_name} does not exist.")

    if open(test_error_file_name, 'r').read() != "":
        print(f"{test_error_file_name} is nonempty") #Maybe this should just throw an error, but openfoam does this one a lot

    control_execution_time = None
    execution_time = None
    control_comm_pct = None
    comm_pct = None

    # Extract Execution Time value for the control
    control_lines = open(control_test_file_name,'r').read()
    control_execution_time_match = re.findall("ExecutionTime =\s*([\d\.]+)", control_lines)
    if control_execution_time_match:
        control_execution_time = float(control_execution_time_match[-1])

    # Extract Execution Time value
    lines = open(test_file_name,'r').read()
    execution_time_match = re.findall("ExecutionTime =\s*([\d\.]+)", lines)
    if execution_time_match:
        execution_time = float(execution_time_match[-1])

    # Extract Percent Time in Communication
    #comm_pct_match = re.search(r"Comm\s*\|(?:\s*[\d\.]+\s*\|){4}\s*([\d\.]+)", lines)
    #if comm_pct_match:
    #    comm_pct = float(comm_pct_match.group(1))

    if control_execution_time == None:
        raise TestValueError("No value found for the n1_t1 execution time")
    elif execution_time == None:
        raise TestValueError(f"No value found for the n{nodes}_t{tasks} execution time")
    #elif comm_pct == None:
    #    raise TestValueError("No value found for the n{nodes}_t{tasks} Comm Pct")

    parallel_eff = control_execution_time/tasks/execution_time*100
    data = {"openFOAM PE": parallel_eff}
    return data 

# Extracts the results of the nekbone test into a dictionary
def nekbone_results(test_number_directory, test_number, nodes, tasks):
    
    test_file_name = join(test_number_directory, f"nekbone_n{nodes}_t{tasks}.out")
    test_error_file_name = join(test_number_directory, f"nekbone_n{nodes}_t{tasks}.err")
    control_test_file_name = join(test_number_directory, "nekbone_n1_t1.out")

    if not os.path.exists(test_file_name):
        raise FileNotFoundError(f"The file {test_file_name} does not exist.")

    if not os.path.exists(control_test_file_name):
        raise FileNotFoundError(f"The file {control_test_file_name} does not exist.")

    if open(test_error_file_name, 'r').read() != "":
        print(f"{test_error_file_name} is nonempty") #Maybe this should just throw an error, but openfoam does this one a lot

    control_execution_time = None
    execution_time = None
    control_comm_pct = None
    comm_pct = None

    # Extract Execution Time value for the control
    control_lines = open(control_test_file_name,'r').read()
    control_execution_time_match = re.findall("Solve Time =\s*([\d\.E+\d]+)", control_lines)
    if control_execution_time_match:
        control_execution_time = float(control_execution_time_match[-1])

    # Extract Execution Time value
    lines = open(test_file_name,'r').read()
    execution_time_match = re.findall("Solve Time =\s*([\d\.E+\d]+)", lines)
    if execution_time_match:
        execution_time = float(execution_time_match[-1])

    # Extract Percent Time in Communication
    #comm_pct_match = re.search(r"Comm\s*\|(?:\s*[\d\.]+\s*\|){4}\s*([\d\.]+)", lines)
    #if comm_pct_match:
    #    comm_pct = float(comm_pct_match.group(1))

    if control_execution_time == None:
        raise TestValueError("No value found for the n1_t1 execution time")
    elif execution_time == None:
        raise TestValueError(f"No value found for the n{nodes}_t{tasks} execution time")
    #elif comm_pct == None:
    #    raise TestValueError("No value found for the n{nodes}_t{tasks} Comm Pct")

    parallel_eff = control_execution_time/execution_time*100
    data = {"Nekbone PE": parallel_eff}
    return data 


args_dict = {}

if __name__ == "__main__":

    # Create the parser
    parser = argparse.ArgumentParser(description='Collates information from a series of test runs of a program on a slurm cluster')

    parser.add_argument('--test-number', required=True,type=str, help='Name of a series of test')
    # Parse arguments
    args = parser.parse_args()
    args_dict = vars(args)
    
    test_number = args_dict["test_number"]

    # Load the output files 
    test_number_directory = join("benchmark_results",test_number)
    if not os.path.exists(test_number_directory):
        raise FileNotFoundError(f"The directory {test_number_directory} does not exist.")

    node_file = join(test_number_directory,"node_tuples.txt")
    if not os.path.exists(node_file):
        raise FileNotFoundError(f"The file {node_file} does not exist.")
 

    system_info_dict = {}
    sys_info_file = join(test_number_directory,"sys_info.txt")
    if not os.path.exists(sys_info_file):
        raise FileNotFoundError(f"The file {sys_info_file} does not exist.")
    else:
        sys_info =  open(sys_info_file, "r")
        system_info_dict = eval(sys_info.read())

    # Load the CSV file
    csv_path = f"results.csv"
    results_df = ensure_csv(csv_path)
 
    # Load the node_tuples.txt
    for nodes, tasks in open_tuple_file(node_file):

        new_test_results = dict.fromkeys(column_names, None)
        lammps_dict = lammps_results(test_number_directory, test_number, nodes, tasks) #THis should check for existence of the lamps file, and if it produces a naan should atleast throw a warning
        new_test_results.update(lammps_dict)

        openfoam_dict = openfoam_results(test_number_directory, test_number, nodes, tasks)
        new_test_results.update(openfoam_dict)

        nekbone_dict = nekbone_results(test_number_directory, test_number, nodes, tasks)
        new_test_results.update(nekbone_dict)
 
        
        #Update the test results with the system info from the tests
        new_test_results['Nodes'] = nodes
        new_test_results['Tasks'] = tasks
        new_test_results['Test Number'] = test_number
        new_test_results.update(system_info_dict)

        new_test_row = pd.DataFrame([new_test_results]).set_index("Test Number")
        results_df = pd.concat([results_df, new_test_row])


    # Update the .csv file
    results_df.to_csv(csv_path)

