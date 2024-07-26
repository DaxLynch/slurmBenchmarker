import argparse
import subprocess
import os
from os.path import join
import math
import shutil

#The way this benchmarker should work, is a specfic exe will get called by srun with varying amounts of nodes and tasks. By altering which create_sbatch_script_* function gets called, it should vary which exe. I plan on making this for every one of these programs which I am going to bnchmark. I will then have a separate function combs through the returned results.

#Assumptions: Running on a slurm HPC cluster
#Currently: Wanting to benchmark lammps leonard jones style simulation
#Future: Wanting to benchmark various hpc programs


# Create the parser
parser = argparse.ArgumentParser(description='Submits a series of test runs of a program on a slurm cluster')

parser.add_argument('--test-series', required=True,type=str, help='Name of a series of test')
parser.add_argument('--tuples',      required=True,type=str, help='Series of (node,task) tuples for the tests')
parser.add_argument('--program',     required=True,type=str, help='Program you are benchmarking, options are: lammps')
parser.add_argument('--size',        required=True,type=str, help='Whether or not the problem size is fixed or free', default="fixed")

# Parse arguments
args = parser.parse_args()
args_dict = vars(args)

# Define a function to create sbatch script content
def create_sbatch_script_lammps(nodes, tasks, job_name, directives, environments):
    assert math.log2(tasks) == int(math.log2(tasks)) #Tasks must be power of two, I think this is an arbitrary decsion
    x = int(2**math.floor(math.log2(tasks)/3))
    y = int(2**math.ceil(math.log2(tasks)/3))
    z = y #Lammps requires being given a x y and z grid to separate the work into
          # This code above breaks the tasks respective sizes.

    ret =  f"""#!/bin/bash
#SBATCH --job-name={job_name} 
#SBATCH --nodes={nodes}
#SBATCH --ntasks={tasks}
#SBATCH --ntasks-per-node={tasks // nodes}
#SBATCH -t 0-0:10
#SBATCH --output=benchmark_results/{args_dict["test_series"]}/{job_name}.out
#SBATCH --error=benchmark_results/{args_dict["test_series"]}/{job_name}.err
{directives}

{environments}

# Execute LAMMPS with srun and capture detailed timing

""" 
    if tasks == 1:
        return ret + f"srun lmp -in in.lj -log benchmark_results/{args_dict['test_series']}/log.lammps"
    elif args_dict["size"] == "fixed":
        return ret + f"srun -n {tasks} lmp -in in.lj -log benchmark_results/{args_dict['test_series']}/log.lammps"
    else:
        return ret + f"srun -n {tasks} lmp -var x {x} -var y {y} -var z {z} -in in.lj -log benchmark_results/{args_dict['test_series']}/log.lammps"

# Function to submit the sbatch script
def submit_sbatch_script(script_content, job_name):
    script_file = f"benchmark_results/{args_dict['test_series']}/{job_name}.sbatch"
    with open(script_file, 'w') as f:
        f.write(script_content)
    subprocess.run(['sbatch', script_file])

def ensure_directories():
    test_run = args_dict["test_series"]
    #This makes the respective directories if they aren't made
    dir_name = 'benchmark_results'
    if os.path.exists(dir_name):
        if os.path.exists(join(dir_name,test_run)): #Overwrite if this is the second time
            print("Overwriting previous runs")
            shutil.rmtree(join(dir_name,test_run)) 
        os.makedirs(join(dir_name,test_run)) 
    else:
        os.makedirs(dir_name) 
        os.makedirs(join(dir_name,test_run)) 
    
    #Each machine has specific environment and directive codes, such as account#, etc.
    #This ensures your srun command runs with proper directives and environment
    directives_file = open("machine_specific_sbatch_directives.txt",'r')
    environments_file = open("machine_specific_sbatch_environments.txt",'r')
    directives = directives_file.read()
    environments = environments_file.read()

    return (directives, environments)

if __name__ == "__main__":
    directives, environments = ensure_directories()
    node_task_tuples = open(args_dict["tuples"],'r').readlines()
    for task_tuple in node_task_tuples:
        task_tuple = task_tuple.split()
        nodes = int(task_tuple[0])
        tasks = int(task_tuple[1])
        if args_dict["program"] == "lammps":
            job_name = f"lammps_n{nodes}_t{tasks}"
            script_content = create_sbatch_script_lammps(nodes, tasks, job_name, directives, environments)
            submit_sbatch_script(script_content, job_name)
            print(f"Submitted job: {job_name}")


