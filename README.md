This Repo is meant to aid me in benchmarking various programs that run on slurm, with the goal of comparing performance across multiple HPC systems.

It uses the node_tuples.txt to submit multiple slurm sbatch scripts with varying node and task sizes, so you can see how performance scales with inter- and intranode communication.
To run, alter the node_tuples.txt to show how many runs you want of specfic sizes, the two numbers representing nodes and tasks respective, with it assumed you want ntasks-per-node=nodes//tasks

If running on perlmutter, alter the below line:
#SBATCH -A ###CHANGE ME TO YOUR PERLMUTTER ACCOUNT NUMBER###

Then call slurm_benchmarker with a name for the series of tests you want to run, labeled test-series, the file pointing to the tuples, which program you are wishing to record, and whether or not you want the size of the problem to scale, and which machine you are calling on. 

Once these have all returned, call slurm_logviz with similar commands.

for example:
with the given node_tuples.txt,

python slurm_benchmarker.py --test-series=NameOfTest --tuples=node_tuples.txt --program=lammps --scaling=free --machine=perlmutter --length=short
python -i slurm_logvis.py --test-series=OneNodeRun --program=lammps --scaling=fixed --graph=False --length=short

Note do not put senistive data like account numbers in the machine specific directives



