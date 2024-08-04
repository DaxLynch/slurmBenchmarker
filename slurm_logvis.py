import argparse
import os
from os.path import join
import pandas as pd
import matplotlib.pyplot as plt

#the way this should work is it should get called after your slurm jobs have finished.
#Given the name of a run it collates all information for that job type into python data
# and prints a txt output for it.
#I want something to do with printing graphs or making outputs but since im ssh'd in idk.
#I might output to jpeg and then move it to a different server.

#Assumptions: Running on a slurm HPC cluster
#Currently: Wanting to benchmark lammps leonard jones style simulation
#Future: Wanting to benchmark various hpc programs

args_dict = {}

def lammps_graph(file_path_to_results_csv):
    data=pd.read_csv(file_path_to_results_csv, index_col="Tasks")
    path_to_results = file_path_to_results_csv[:file_path_to_results_csv.find(".csv")]
    
    grouped = data.groupby('Nodes')
    # Plot each group with a different color
    for name, group in grouped:
        plt.plot(group.index, group['Parallel Eff'], marker='o', linestyle='-', label=f'{name} Nodes')

    plt.xlabel('Number of Tasks')
    plt.ylabel('Parallel Efficiency (%)')
    plt.ylim(0,100)
    plt.title('Parallel Efficiency vs Number of Tasks for Different Node Configurations')
    plt.legend(title='Number of Nodes')
    plt.grid(True)
    plt.savefig(f"{path_to_results}ParaEff.png")
    plt.show()
    plt.clf()

    # Plot each group's percent time in communication with a different color
    for name, group in grouped:
        plt.plot(group.index, group['Comm Pct'], marker='o', linestyle='-', label=f'{name} Nodes')

    plt.xlabel('Number of Tasks')
    plt.ylabel('Percent Time in MPI Comm')
    plt.ylim(0,100)
    plt.title('Percent Time in MPI Comm vs Number of Tasks for Different Node Configurations')
    plt.legend(title='Number of Nodes')
    plt.grid(True)
    plt.savefig(f"{path_to_results}CommPct.png")
    plt.show() 
    plt.clf()

# Define a function to read the data from a series of lammps runs
# returns a pandas df
def lammps(test_series_name): #results is a list of tuples of files and their names.
    test_series_directory = join("benchmark_results",test_series_name)
    if not os.path.exists(test_series_directory):
        raise FileNotFoundError(f"The directory {test_series_directory} does not exist.")

    file_walk = os.walk(test_series_directory)
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
        SingleProcTime = data.at[1,"Wall Time"] #ASSUMING THERE IS A 1 NODE 1 TASK
        if args_dict["scaling"] == "fixed":
            data["Parallel Eff"] = SingleProcTime/(data["Wall Time"]*data.index)*100
        else:
            data["Parallel Eff"] = SingleProcTime/data["Wall Time"]*100
        data.to_csv(join(test_series_directory,test_series_name)+"Results.csv")
    if args_dict["graph"] == "True":
        lammps_graph(join(test_series_directory,test_series_name)+"Results.csv")

    return data 

results = None
if __name__ == "__main__":

    # Create the parser
    parser = argparse.ArgumentParser(description='Collates information from a series of test runs of a program on a slurm cluster')

    parser.add_argument('--test-series', required=True,type=str, help='Name of a series of test')
    parser.add_argument('--program',     required=True,type=str, help='Program you are benchmarking, options are: lammps')
    parser.add_argument('--scaling',     required=True,type=str, help='Whether or not the problem scaling is fixed or free', default="fixed")
    parser.add_argument('--graph',       required=False,type=str, help='Whether to produce relevant graphs, options are: True, False', default="False")

    # Parse arguments
    args = parser.parse_args()
    args_dict = vars(args)
    test_series_name = args_dict['test_series']+args_dict['scaling']
    test_series_directory = join("benchmark_results",test_series_name)
    if not os.path.exists(test_series_directory):
        raise FileNotFoundError(f"The directory {test_series_directory} does not exist.")
    if args_dict["program"] == "lammps":
        results = lammps(args_dict["test_series"]+args_dict["scaling"])


