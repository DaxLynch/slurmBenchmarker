import subprocess
import pandas as pd
import time
import argparse
import subprocess
import os
from os.path import join
import math
import shutil

args_dict = {}
column_names = ["Test Number", "Date", "Nodes", "Tasks","Provider", "Instance Type", "OS Version","Lammps PE","Lammps PCTComm","openFOAM PE","Nekbone PE"]


#---------------------------------LAMMPS---------------------------------------

# Define a function to create sbatch script content
def create_sbatch_script_lammps(test_number, nodes, tasks, job_name):
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
    slurm_flags = args_dict["slurm_flags"]  
    length = f"program_files/{args_dict['length']}.lj"


    if args_dict["provider"] == "aws":          #The below are the machine specific directives and environment variables
                                               #required for slurm
        directives =  """#SBATCH --exclusive"""
        environments= """#Set environment variables
export MV2_HOMOGENEOUS_CLUSTER=1
export MV2_SUPPRESS_JOB_STARTUP_PERFORMANCE_WARNING=1
# Load LAMMPS
spack load --first lammps"""
    elif args_dict["provider"] == "perlmutter":  #Perlmutter specific directives
        directives =  """#SBATCH --image docker:nersc/lammps_all:23.08  
#SBATCH -C cpu
#SBATCH -A 
    providers = {'ec2': 'AWS', 'perlmutter':'NERSC'}
#SBATCH -q regular"""
        
        slurm_flags = slurm_flags + "--cpu-bind=cores --module mpich shifter"  #Specific flags for slurm
 
    ret = f"""#!/bin/bash
#SBATCH --job-name={test_number}_{job_name} 
#SBATCH --nodes={nodes}
#SBATCH --ntasks={tasks}
#SBATCH -t 0-0:20
#SBATCH --output=benchmark_results/{test_number}/{job_name}.out
#SBATCH --error=benchmark_results/{test_number}/{job_name}.err
{directives}
export OMP_NUM_THREADS=1
{environments}
""" 
    
    if tasks == 1:
        return ret + f"srun {slurm_flags} lmp -in {length} -log benchmark_results/{test_number}/lammps.log"
    else:
        return ret + f"srun -n {tasks} {slurm_flags} lmp -var x {x} -var y {y} -var z {z} -in {length} -log benchmark_results/{test_number}/lammps.log"

#Submit tests on lammps
def lammps(test_number, nodes, tasks):
    job_name = f"lammps_n{nodes}_t{tasks}"
    script_content = create_sbatch_script_lammps(test_number, nodes, tasks, job_name)
    submit_sbatch_script(test_number, script_content, job_name)
    print(f"Submitted job: {job_name}")



#---------------------------------openFOAM---------------------------------------



# Define a function to create sbatch script content
def create_sbatch_script_openfoam(test_number, nodes, tasks, job_name):
    directives = ""
    environments = ""
    slurm_flags = args_dict["slurm_flags"]  

    job_directory = f"benchmark_results/{test_number}/{job_name}" #For openfoam we need a case directory. In each node tuple we create a new directory, copy in the size test we want, 1M or 8M, and then pase this to each later command

    if args_dict["provider"] == "aws":          #The below are the machine specific directives and environment variables
                                               #required for slurm
        directives =  """#SBATCH --exclusive"""
        environments= """#Set environment variables
export MV2_HOMOGENEOUS_CLUSTER=1
export MV2_SUPPRESS_JOB_STARTUP_PERFORMANCE_WARNING=1
"""
    elif args_dict["provider"] == "perlmutter":  #Perlmutter specific directives
        directives =  """#SBATCH -C cpu
#SBATCH -A 
#SBATCH -q regular"""
        
        slurm_flags = slurm_flags + "--cpu-bind=cores "  #Specific flags for slurm
 
    parallel = "" if tasks == 1 else "-parallel" #Don't add the parallel unless multile processes

    ret = f"""#!/bin/bash
#SBATCH --job-name={test_number}_{job_name} 
#SBATCH --nodes={nodes}
#SBATCH --ntasks={tasks}
#SBATCH -t 0-0:20
#SBATCH --output=benchmark_results/{test_number}/{job_name}.out
#SBATCH --error=benchmark_results/{test_number}/{job_name}.err
{directives}

{environments}
#load openFOAM
spack load --first openfoam
. ${{WM_PROJECT_DIR:?}}/bin/tools/RunFunctions

blockMesh -case {job_directory}
decomposePar -case {job_directory}
srun {slurm_flags} renumberMesh -overwrite {parallel} -case {job_directory}
srun {slurm_flags} icoFoam {parallel} -case {job_directory}
""" 
    return ret

#Submit tests on openfoam
def openfoam(test_number, nodes, tasks):
    job_name = f"openfoam_n{nodes}_t{tasks}"
    if args_dict['length'] == "short":
        shutil.copytree("program_files/openfoam/1M",f"benchmark_results/{test_number}/{job_name}")
    else:
        shutil.copytree("program_files/openfoam/8M",f"benchmark_results/{test_number}/{job_name}")
    
    subprocess.run(["sed", "-i", f"s/numberOfSubdomains 32;/numberOfSubdomains {tasks};/", f"benchmark_results/{test_number}/{job_name}/system/decomposeParDict"])
    script_content = create_sbatch_script_openfoam(test_number, nodes, tasks, job_name)
    submit_sbatch_script(test_number, script_content, job_name)
    print(f"Submitted job: {job_name}")

#-----------------------------------------nekBone-------------------------------------



# Define a function to create sbatch script content
def create_sbatch_script_nekbone(test_number, nodes, tasks, job_name):
    directives = ""
    environments = ""
    slurm_flags = args_dict["slurm_flags"]  

    job_directory = f"benchmark_results/{test_number}/{job_name}" 

    if args_dict["provider"] == "aws":          #The below are the machine specific directives and environment variables
                                               #required for slurm
        directives =  """#SBATCH --exclusive"""
        environments= """#Set environment variables
export MV2_HOMOGENEOUS_CLUSTER=1
export MV2_SUPPRESS_JOB_STARTUP_PERFORMANCE_WARNING=1
"""
    elif args_dict["provider"] == "perlmutter":  #Perlmutter specific directives
        directives =  """#SBATCH -C cpu
#SBATCH -A 
#SBATCH -q regular"""
        
        slurm_flags = slurm_flags + "--cpu-bind=cores "  #Specific flags for slurm
 
    ret = f"""#!/bin/bash
#SBATCH --job-name={test_number}_{job_name} 
#SBATCH --nodes={nodes}
#SBATCH --ntasks={tasks}
#SBATCH -t 0-0:20
#SBATCH --output=benchmark_results/{test_number}/{job_name}.out
#SBATCH --error=benchmark_results/{test_number}/{job_name}.err
{directives}

{environments}
#load nekBone
spack load --first nekbone
export G="-g -fallow-argument-mismatch"
cd {job_directory}
makenek #Maybe silence to devnull

srun {slurm_flags} ./nekbone
""" 
    return ret

#Submit tests on nekbone
def nekbone(test_number, nodes, tasks):
    #This function finds where makenek is, creates a job_directory, copies the test 
    #file SIZE and data.rea into it, alters SIZE and then creates and calls the sbatch
    #script

    job_name = f"nekbone_n{nodes}_t{tasks}"
    job_directory =  f"benchmark_results/{test_number}/{job_name}"
    
    #Copies the test into the directory
    shutil.copytree("program_files/nekbone/",job_directory) 

    #Alters SIZE
    subprocess.run(["sed", "-i", f"s/      parameter (lp = 10)/      parameter (lp = {tasks})/", f"{job_directory}/SIZE"])

    script_content = create_sbatch_script_nekbone(test_number, nodes, tasks, job_name)
    submit_sbatch_script(test_number, script_content, job_name)
    print(f"Submitted job: {job_name}")


#----------------------------Quantum-Espresso-------------------------------------


# Define a function to create sbatch script content
def create_sbatch_script_quantum_espresso(test_number, nodes, tasks, job_name):
    directives = ""
    environments = ""
    slurm_flags = args_dict["slurm_flags"]  

    job_directory = f"benchmark_results/{test_number}/{job_name}" 

    if args_dict["provider"] == "aws":          #The below are the machine specific directives and environment variables
                                               #required for slurm
        directives =  """#SBATCH --exclusive"""
        environments= """#Set environment variables
export MV2_HOMOGENEOUS_CLUSTER=1
export MV2_SUPPRESS_JOB_STARTUP_PERFORMANCE_WARNING=1
"""
    elif args_dict["provider"] == "perlmutter":  #Perlmutter specific directives
        directives =  """#SBATCH -C cpu
#SBATCH -A 
#SBATCH -q regular"""
        
        slurm_flags = slurm_flags + "--cpu-bind=cores "  #Specific flags for slurm
 
    ret = f"""#!/bin/bash
#SBATCH --job-name={test_number}_{job_name} 
#SBATCH --nodes={nodes}
#SBATCH --ntasks={tasks}
#SBATCH -t 0-0:20
#SBATCH --output=benchmark_results/{test_number}/{job_name}.out
#SBATCH --error=benchmark_results/{test_number}/{job_name}.err
{directives}

{environments}
#load nekBone
spack load --first quantum_espresso
export G="-g -fallow-argument-mismatch"
cd {job_directory}
makenek #Maybe silence to devnull

srun {slurm_flags} ./quantum_espresso
""" 
    return ret

#Submit tests on quantum_espresso
def quantum_espresso(test_number, nodes, tasks):

    job_name = f"quantum_espresso_n{nodes}_t{tasks}"
    job_directory =  f"benchmark_results/{test_number}/{job_name}"
    
    #Copies the test into the directory ## We need the test file to be correct tho
    #test file must alter ./tmp/file
    #Alter k to be equal to calculated xK
    #I want this problem to scale with the number of processors. So no matter how many
    #processors you run it on, it should always take about as long as the control
    #and the ratio of the ControlTime/eXperimentalTime aka cTime/xTime, is the parallel efficiency
    #The variable that determines computational complexity is K^3. So cK is K for the control. cK = 15, so cK^3 = 3375. I then need to find the eXperimental K, xK, so that the eXperimental time is approximately cTime.
    #Via some algebra xK is (cK^3*nProc)^(1/3) and since K needs to be an integer, we round it.
    #But since it is not exact it means the xTime is not exactly equal to cTime,
    #So via some algebra xTime = cTime * (xK/cK)^3/nProc.
    cK = 15 #K value for nProc = 1
    xK = round((cK**3 * tasks)**(1/3))

    os.makedirs(job_directory, exist_ok=True)
    input_file_template_lines = open("program_files/quantum_espresso/pw.scf.in",'r').readlines()
    input_file_template_lines[-1] = f"  {xK} {xK} {xK} 1 1 1 \n"
    input_file_template_lines[8] = f"  outdir = {job_directory} \n"
    
    input_file = open(job_directory+"/pw.scf.in",'w')
    input_file.write("".join(input_file_template_lines))
    input_file.close()    



#   script_content = create_sbatch_script_quantum_espresso(test_number, nodes, tasks, job_name)
#   submit_sbatch_script(test_number, script_content, job_name)
    print(f"Submitted job: {job_name}")




#----------------------------------Utils-------------------------------------------

# Function to submit the sbatch script
def submit_sbatch_script(test_number, script_content, job_name):
    script_file = f"benchmark_results/{test_number}/{job_name}.sbatch"
    with open(script_file, 'w') as f:
        f.write(script_content)
#    subprocess.run(['sbatch', script_file])

#Ensures that the directory required for the tests is created.
def ensure_directories(test_number):     
    dir_name = 'benchmark_results'
    if os.path.exists(dir_name):
        os.makedirs(join(dir_name,test_number)) 
    else:
        os.makedirs(dir_name) 
        os.makedirs(join(dir_name,test_number))     

#Ensures that the csv is created and well formed
def ensure_csv(csv_path):
    results_df = None
    if os.path.exists(csv_path):
        results_df = pd.read_csv(csv_path, index_col="Test Number")
    else:
        results_df = pd.DataFrame(columns=column_names).set_index("Test Number")      
        results_df.to_csv(csv_path)
    return results_df

class TestTupleError(Exception):
    """Whenever tests are done, they should be completed at minimum on 1 node and 1 task (1,1), and 4 node and 64 tasks. This is to ensure some measure of comparison"""
    def __init__(self, message="Control tuple(s) not found"):
        self.message = message
        super().__init__(self.message)

#Returns a list of tuples, with each tuple representing (# of Nodes, # of tasks) for each slurm job
def open_tuple_file(file_name):
    tuple_lines = open(file_name,'r').readlines()
    ret = []
    for node_task in tuple_lines:
        nodes = int(node_task.split()[0])
        tasks = int(node_task.split()[1])
        ret.append((nodes,tasks))

    if (1,1) not in ret or (4,64) not in ret:
        raise TestTupleError()
    return ret

#writes the node_tuple.txt file and the sys_info.txt file
def write_system_info(new_test_number):
    shutil.copy(args_dict["tuples"], join("benchmark_results", new_test_number, "node_tuples.txt"))        
    instance_type = args_dict['instance_type']
    os_version = args_dict['os_version']
    provider = args_dict['provider']

    with open(join("benchmark_results",new_test_number,"sys_info.txt"), "w+") as sys_info:
        system_info_dict = {'Instance Type':instance_type,'Provider':provider, 'OS Version':os_version, 'Date':time.ctime(int(new_test_number))}
        sys_info.write(str(system_info_dict))

def parse_args():

    # Create the parser
    parser = argparse.ArgumentParser(description='Submits a series of test runs of a program on a slurm cluster')

    parser.add_argument('--provider',      required=True,  type=str.lower, help='HPC system you are benchmarking, options are: aws, perlmutter', choices=['aws', 'perlmutter'])
    parser.add_argument('--tuples',        required=False, type=str, help='Series of (node,task) tuples for the tests', default="node_tuples.txt")
    parser.add_argument('--slurm-flags',   required=False, type=str, help='Machine specfic flags to be passed to srun', default="")
    parser.add_argument('--length',        required=False, type=str, help='Length of test to run, options are: short, long', default="short", choices=['short','long'])
    parser.add_argument('--instance-type', required=True, type=str.lower, help='Type of compute node')
    parser.add_argument('--os-version',    required=False, type=str.lower, help='OS Version, options are: ubuntu2204', default="ubuntu2204", choices=['ubuntu2204'])

    # Parse arguments
    args = parser.parse_args()
    
    return args




if __name__ == "__main__":


    args = parse_args()
    args_dict = vars(args)


    # Load the CSV file
    csv_path = f"results.csv"
    results_df = ensure_csv(csv_path)

    new_test_number = str(int(time.time())) #Each test is given the time it is called, this is an easy way to ensure that two machines don't try to do test with the same test number, as they probably wont be called at the same nanosecond 
    
    ensure_directories(new_test_number)

    write_system_info(new_test_number)
 
    for nodes, tasks in open_tuple_file(args_dict["tuples"]):
    #    lammps(new_test_number, nodes, tasks)
     #   openfoam(new_test_number, nodes, tasks)
      #  nekbone(new_test_number, nodes, tasks)
        quantum_espresso(new_test_number, nodes, tasks)

   
