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
        print("SUCCESS time found")

    # Extract Percent Time in Communication
    comm_pct_match = re.search(r"Comm\s*\|(?:\s*[\d\.]+\s*\|){4}\s*([\d\.]+)", lines)
    if comm_pct_match:
        print("SUCCESS comm pct found")
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
  
    # Load the CSV file
    csv_path = f"results.csv"
    results_df = ensure_csv(csv_path)
 
    # Load the node_tuples.txt
    for nodes, tasks in open_tuple_file(node_file):

        new_test_results = dict.fromkeys(column_names, None)
        lammps_dict = lammps_results(test_number_directory, test_number, nodes, tasks) #THis should check for existence of the lamps file, and if it produces a naan should atleast throw a warning
        new_test_results.update(lammps_dict)

    #   openFOAM_results = openFOAM(test_number, nodes, tasks)
    #   new_test_results.update(openFOAM_results)
        
        new_test_row = pd.DataFrame([new_test_results]).set_index("Test Number")
        results_df = pd.concat([results_df, new_test_row])


    # Update the .csv file
    results_df.to_csv(csv_path)

