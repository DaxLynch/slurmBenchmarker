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
parser.add_argument('--machine',     required=True,type=str, help='HPC system you are benchmarking, options are: ec2, perlmutter')
parser.add_argument('--scaling',        required=True,type=str, help='Whether or not the problem scaling is fixed or free', default="fixed")
parser.add_argument('--slurm-flags', required=False,type=str, help='Machine specfic flags to be passed to srun', default="")

# Parse arguments
args = parser.parse_args()
args_dict = vars(args)

# Define a function to create sbatch script content
def create_sbatch_script_lammps(nodes, tasks, job_name):
    assert math.log2(tasks) == int(math.log2(tasks)) #Tasks must be power of two, I think this is an arbitrary decsion
    x = 1
    y = 1
    z = 1
    if tasks == 2:
        x = 2
    if tasks > 2:
        x = int(2**math.floor(math.log2(tasks)/3))
        y = int(2**math.ceil(math.log2(tasks)/3)) 
        z = int(2**(math.log2(tasks) - math.log2(x) - math.log2(y))) #Lammps requires being given a x y and z grid to separate the work into
              # This code above breaks the tasks respective sizes.
    directives = ""
    environments = ""
    slurm_flags = args_dict["slurm_flags"]  
    if args_dict["machine"] == "ec2":
        directives =  """#SBATCH --exclusive
"""
        environments= """#Set environment variables
export MV2_HOMOGENEOUS_CLUSTER=1
export MV2_SUPPRESS_JOB_STARTUP_PERFORMANCE_WARNING=1

# Load LAMMPS
spack load --first lammps       
"""
    elif args_dict["machine"] == "perlmutter":
        directives =  """#SBATCH --image docker:nersc/lammps_all:23.08
#SBATCH -C cpu
#SBATCH -A ###CHANGE ME TO YOUR PERLMUTTER ACCOUNT NUMBER###
#SBATCH -q regular
"""
        slurm_flags = slurm_flags + "--cpu-bind=cores --module mpich shifter"
 
    ret = f"""#!/bin/bash
#SBATCH --job-name={job_name} 
#SBATCH --nodes={nodes}
#SBATCH --ntasks={tasks}
#SBATCH -t 0-0:10
#SBATCH --output=benchmark_results/{args_dict["test_series"]}/{job_name}.out
#SBATCH --error=benchmark_results/{args_dict["test_series"]}/{job_name}.err
{directives}

export OMP_NUM_THREADS=1
{environments}

""" 
    if tasks == 1:
        return ret + f"srun {slurm_flags} lmp -in in.lj -log benchmark_results/{args_dict['test_series']}/log.lammps"
    elif args_dict["scaling"] == "fixed":
        return ret + f"srun -n {tasks} {slurm_flags} lmp -in in.lj -log benchmark_results/{args_dict['test_series']}/log.lammps"
    else:
        return ret + f"srun -n {tasks} {slurm_flags} lmp -var x {x} -var y {y} -var z {z} -in in.lj -log benchmark_results/{args_dict['test_series']}/log.lammps"

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

def open_tuple_file(file_name):
    tuple_lines = open(file_name,'r').readlines()
    ret = []
    for node_task in tuple_lines:
        nodes = int(node_task.split()[0])
        tasks = int(node_task.split()[1])
        ret.append((nodes,tasks))
    return ret

if __name__ == "__main__":
    ensure_directories()
    for nodes, tasks in open_tuple_file(args_dict["tuples"]):
        if args_dict["program"] == "lammps":
            job_name = f"lammps_n{nodes}_t{tasks}"
            script_content = create_sbatch_script_lammps(nodes, tasks, job_name)
            submit_sbatch_script(script_content, job_name)
            print(f"Submitted job: {job_name}")


