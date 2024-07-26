import subprocess
import os
import math
import shutil

#The way this benchmarker should work, is a specfic exe will get called by srun with varying amounts of nodes and tasks. By altering which create_sbatch_script_* function gets called, it should vary which exe. I plan on making this for every one of these programs which I am going to bnchmark. I will then have a separate function combs through the returned results.

#Assumptions: Running on a slurm HPC cluster
#Currently: Wanting to benchmark lammps leonard jones style simulation
#Future: Wanting to benchmark various hpc programs


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
#SBATCH --output=benchmark_results/{test_run}/{job_name}.out
#SBATCH --error=benchmark_results/{test_run}/{job_name}.err
{directives}

{environments}

# Execute LAMMPS with srun and capture detailed timing

""" 
    if tasks == 1:
        return ret + f"srun lmp -in in.lj -log benchmark_results/{test_run}/log.lammps"
    elif "size" in kwargs and kwargs["size"] == "fixed":
        return ret + f"srun -n {tasks} lmp -in in.lj -log benchmark_results/{test_run}/log.lammps"
    else:
        return ret + f"srun -n {tasks} lmp -var x {x} -var y {y} -var z {z} -in in.lj -log benchmark_results/{test_run}/log.lammps"

# Function to submit the sbatch script
def submit_sbatch_script(script_content, job_name):
    script_file = f"benchmark_results/{test_run}/{job_name}.sbatch"
    with open(script_file, 'w') as f:
        f.write(script_content)
    subprocess.run(['sbatch', script_file])

# Main function
def main(node_task_tuples):
    # Directory name
    dir_name = 'benchmark_results'
    if os.path.exists(dir_name):
        if os.path.exists(dir_name+"/"+test_run):
            shutil.rmtree(dir_name+"/"+test_run) 
            # Create the directory
            os.makedirs(dir_name+"/"+test_run) 
        else: 
            os.makedirs(dir_name+"/"+test_run) 
    else:
        os.makedirs(dir_name) 
        os.makedirs(dir_name+"/"+test_run) 
    
    directives_file = open("machine_specific_sbatch_directives.txt",'r')
    environments_file = open("machine_specific_sbatch_environments.txt",'r')
    directives = directives_file.read()
    environments = environments_file.read()
    for task_tuple in node_task_tuples:
        nodes = task_tuple[0]
        tasks = task_tuple[1]
        kwargs = task_tuple[2:]
        job_name = f"lammps_n{nodes}_t{tasks}"
        script_content = create_sbatch_script_lammps(nodes, tasks, job_name, directives, environments)
        submit_sbatch_script(script_content, job_name)
        print(f"Submitted job: {job_name}")

if __name__ == "__main__":
    # Define the array of tuples representing (nodes, tasks, kwargs)
    global test_run
    test_run = "scaledRunsOneNode"
    global kwargs
    kwargs={"size" : "scaled"} #These are arguments for specfic programs runs that I don't want to put in each tuple
    node_task_tuples = [
        (1, 1),
        (1, 2),
        (1, 4),
        (1, 8),
        (1, 16),
        (1, 32),
        # Add more tuples as needed
    ]
    main(node_task_tuples)

