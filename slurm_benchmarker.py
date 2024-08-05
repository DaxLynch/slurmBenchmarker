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

parser.add_argument('--test-series', required=True,  type=str, help='Name of a series of test')
parser.add_argument('--tuples',      required=True,  type=str, help='Series of (node,task) tuples for the tests')
parser.add_argument('--program',     required=True,  type=str, help='Program you are benchmarking, options are: lammps')
parser.add_argument('--machine',     required=True,  type=str, help='HPC system you are benchmarking, options are: ec2, perlmutter')
parser.add_argument('--scaling',     required=False, type=str, help='Whether or not the problem scaling is fixed or free', default="free")
parser.add_argument('--slurm-flags', required=False, type=str, help='Machine specfic flags to be passed to srun', default="")
parser.add_argument('--length',      required=False, type=str, help='Length of test to run, options are: short, long', default="short")
parser.add_argument('--tau',         required=False, type=str, help='Whether or not to profile with tau, options are false, true', default="false")

# Parse arguments
args = parser.parse_args()
args_dict = vars(args)
for key in args_dict.keys(): #Makes every arg lowercase for string comparison
    if key != "test_series":
        args_dict[key] = args_dict[key].lower()


# Define a function to create sbatch script content
def create_sbatch_script_lammps(nodes, tasks, job_name):
    assert math.log2(tasks) == int(math.log2(tasks)) #I decided task size should be in powers of two, for ease of testing.
    x = 1
    y = 1
    z = 1
    if tasks == 2:
        x = 2
    if tasks > 2:
        x = int(2**math.floor(math.log2(tasks)/3))
        y = int(2**math.ceil(math.log2(tasks)/3)) 
        z = int(2**(math.log2(tasks) - math.log2(x) - math.log2(y))) #Lammps requires being given a x y and z grid to separate the work into
              # This code above breaks the number of tasks, say 256, into an x y z cube of 4 * 8 * 8 

    directives = ""
    environments = ""
    tau = ""
    slurm_flags = args_dict["slurm_flags"]  
    length = f"{args_dict['length']}.lj"

    test_name_with_modifiers = args_dict['test_series']+args_dict['scaling']+args_dict['length']

    if args_dict['tau'] == "true":
        tau = tau + f"""export PROFILEDIR=benchmark_results/{test_name_with_modifiers}/
export TAU_COMM_MATRIX=1
export TAU_PROFILE_FORMAT=merged"""
        slurm_flags = "tau_exec " + slurm_flags 

    if args_dict["machine"] == "ec2":          #The below are the machine specific directives and environment variables
                                               #required for slurm
        directives =  """#SBATCH --exclusive"""
        environments= """#Set environment variables
export MV2_HOMOGENEOUS_CLUSTER=1
export MV2_SUPPRESS_JOB_STARTUP_PERFORMANCE_WARNING=1
# Load LAMMPS
spack load --first lammps"""
    elif args_dict["machine"] == "perlmutter":  #Perlmutter specific directives
        directives =  """#SBATCH --image docker:nersc/lammps_all:23.08  
#SBATCH -C cpu
#SBATCH -A 
#SBATCH -q regular"""
        if args_dict['tau'] == "true": #How to load tau on perlmutter
            tau = tau + f"""module load e4s
spack env activate gcc
spack load tau"""
        slurm_flags = slurm_flags + "--cpu-bind=cores --module mpich shifter"  #Specific flags for slurm
 
    ret = f"""#!/bin/bash
#SBATCH --job-name={job_name} 
#SBATCH --nodes={nodes}
#SBATCH --ntasks={tasks}
#SBATCH -t 0-0:10
#SBATCH --output=benchmark_results/{test_name_with_modifiers}/{job_name}.out
#SBATCH --error=benchmark_results/{test_name_with_modifiers}/{job_name}.err
{directives}
export OMP_NUM_THREADS=1
{environments}
{tau}
""" 
    
    if tasks == 1:
        return ret + f"srun {slurm_flags} lmp -in {length} -log benchmark_results/{test_name_with_modifiers}/log.lammps"
    elif args_dict["scaling"] == "fixed":
        return ret + f"srun -n {tasks} {slurm_flags} lmp -in {length} -log benchmark_results/{test_name_with_modifiers}/log.lammps"
    else:
        return ret + f"srun -n {tasks} {slurm_flags} lmp -var x {x} -var y {y} -var z {z} -in {length} -log benchmark_results/{test_name_with_modifiers}/log.lammps"

# Function to submit the sbatch script
def submit_sbatch_script(script_content, job_name):
    test_name_with_modifiers = args_dict['test_series']+args_dict['scaling']+args_dict['length'] 
    script_file = f"benchmark_results/{test_name_with_modifiers}/{job_name}.sbatch"
    with open(script_file, 'w') as f:
        f.write(script_content)
    subprocess.run(['sbatch', script_file])

#Ensures that the directory required for the test you want to run exist, and if not, creates it
def ensure_directories():      
    test_run = args_dict['test_series']+args_dict['scaling']+args_dict['length'] 
    dir_name = 'benchmark_results'
    if os.path.exists(dir_name):
        if os.path.exists(join(dir_name,test_run)): #Overwrite if this is the second time
            print("Overwriting previous runs")
            shutil.rmtree(join(dir_name,test_run)) 
        os.makedirs(join(dir_name,test_run)) 
    else:
        os.makedirs(dir_name) 
        os.makedirs(join(dir_name,test_run))     

def open_tuple_file(file_name): #Returns a list of tuples, with each tuple representing (# of Nodes, # of tasks) for each slurm job
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


