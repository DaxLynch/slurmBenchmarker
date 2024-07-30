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
parser.add_argument('--scaling',        required=True,type=str, help='Whether or not the problem scaling is fixed or free', default="fixed")
parser.add_argument('--graph',       required=False,type=bool, help='Whether to produce relevant graphs', default=False)

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
        SingleProcTime = data.at[1,"Nodes"] #ASSUMING THERE IS A 1 NODE 1 TASK
        if args_dict["scaling"] == "fixed":
            data["Parallel Eff"] = SingleProcTime/(data["Wall Time"]*data.index)
        else:
            data["Parallel Eff"] = SingleProcTime/data["Wall Time"]
        data.to_csv(join(root,test_series)+"Results.csv")
   
    if args_dict["graph"]:
        grouped = df.groupby('Nodes')
        # Plot each group with a different color
        for name, group in grouped:
            plt.plot(group.index, group['Parallel Eff']*100, marker='o', linestyle='-', label=f'{name} Nodes')

        plt.xlabel('Number of Tasks')
        plt.ylabel('Parallel Efficiency (%)')
        plt.ylim(0,100)
        plt.title('Parallel Efficiency vs Number of Tasks for Different Node Configurations')
        plt.legend(title='Number of Nodes')
        plt.grid(True)
        plt.savefig(f"{test_series}ParaEff{args_dict["scaling"]}",format="png")
        plt.show()

        # Plot each group's percent time in communication with a different color
        for name, group in grouped:
            plt.plot(group.index, group['Comm Pct'], marker='o', linestyle='-', label=f'{name} Nodes')

        plt.xlabel('Number of Tasks')
        plt.ylabel('Percent Time in MPI Comm')
        plt.ylim(0,100)
        plt.title('Percent Time in MPI Comm vs Number of Tasks for Different Node Configurations')
        plt.legend(title='Number of Nodes')
        plt.grid(True)
        plt.savefig(f"{test_series}CommPct{args_dict["scaling"]}",format="png")
        plt.show() 
                
    return data 

results = None
if __name__ == "__main__":
    if not os.path.exists(join("benchmark_results", args_dict['test_series'])):
        raise FileNotFoundError(f"The directory {join('benchmark_results', test_series)} does not exist.")
    if args_dict["program"] == "lammps":
        results = lammps(args_dict["test_series"])


