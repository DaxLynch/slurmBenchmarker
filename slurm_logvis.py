import argparse
import os
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

parser.add_argument('--test-series', required=True,type=str, help='Name of a series of test')
parser.add_argument('--program',     required=True,type=str, help='Program you are benchmarking, options are: lammps')

# Parse arguments
args = parser.parse_args()
args_dict = vars(args)

# Define a function to read the data from a series of lammps runs
# returns a pandas df
def lammps(test_series): #results is a list of tuples of files and their names.
    if not os.path.exists(join("benchmark_results", test_series)):
        raise FileNotFoundError(f"The directory {join('benchmark_results', test_series)} does not exist.")

    file_walk = os.walk(join("benchmark_results", test_series))
    data = pd.DataFrame(columns=["Tasks","Nodes","Wall Time","Atoms","Matom-step/s","Comm Pct","CPU Pct"])
    for root, _, files in file_walk:
        files.remove("log.lammps")
        for file in files:
            if file.endswith(".out"):  # Assuming log files have .out extension
                file_data = {} #this is very jenky I should have just used re....
                file_data["Nodes"] = int(file.split("_")[1].split("n")[1])
                file_data["Tasks"] = int(file.split("_")[2][1:].split(".")[0])
                result_file_path = os.path.join(root, file)
                lines = open(result_file_path,'r').readlines()
                for line in lines:
                    if "Loop time" in line:
                        file_data['Wall Time'] = float(line.split()[3])
                    elif "Created" in line and "atoms" in line:
                        file_data['Atoms'] = float(line.split()[1])
                    elif "Matom" in line:
                        file_data['Matom-step/s'] = float(line.split()[5])
                    elif "Comm" in line:
                        file_data['Comm Pct'] = float(line.split()[-1])
                    elif "CPU use" in line:
                        file_data['CPU Pct'] = float(line.split()[0][:-1])
                data.loc[len(data)] = file_data
        data.set_index("Tasks",inplace=True,drop=True)
        data.sort_index(inplace=True)
        data.to_csv(join(root,test_series)+"Results.csv")
        
    return data 

results = None
if __name__ == "__main__":
    if args_dict["program"] == "lammps":
        results = lammps(args_dict["test_series"])


