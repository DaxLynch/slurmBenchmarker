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
    plt.xscale("log", base=2);
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
    plt.xscale("log", base=2);
    plt.ylabel('Percent Time in MPI Comm')
    plt.ylim(0,100)
    plt.title('Percent Time in MPI Comm vs Number of Tasks for Different Node Configurations')
    plt.legend(title='Number of Nodes')
    plt.grid(True)
    plt.savefig(f"{path_to_results}CommPct.png")
    plt.show() 
    plt.clf()


