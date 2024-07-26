import argparse
import os
import re
from os.path import join
import pandas as pd


#the way this should work is it should get called after your slurm jobs have finished.
#Given the name of a run it collates all information for that job type into python data
# and prints a txt output for it.
#I want something to do with printing graphs or making outputs but since im ssh'd in idk.
#I might output to jpeg and then move it to a different server.

#Assumptions: Running on a slurm HPC cluster
#Currently: Wanting to benchmark lammps leonard jones style simulation
#Future: Wanting to benchmark various hpc programs


# Create the parser
parser = argparse.ArgumentParser(description='Collates information from a series of test runs of a program on a slurm cluster')

parser.add_argument('--test_series', required=True,type=str, help='Name of a series of test')
parser.add_argument('--program',     required=True,type=str, help='Program you are benchmarking, options are: lammps')

# Parse arguments
args = parser.parse_args()
args_dict = vars(args)

# Define a function to read the data from a series of lammps runs
# returns a pandas df
def lammps(file_walk): #results is a list of tuples of files and their names.
    for root, _, files in file_walk:
        for file in files:
            if file.endswith(".out"):  # Assuming log files have .out extension
                result_file_path = os.path.join(root, file)
                
    data = None
    return data 
if __name__ == "__main__":
    print(args_dict)
    file_walk = os.walk(join("benchmark_results",args_dict["test_series"]))
    if args_dict["program"] == "lammps":
        results = lammps(file_walk)


