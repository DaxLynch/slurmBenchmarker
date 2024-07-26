To run, alter the node_tuples.txt to show how many runs you want of specfic sizes, the two numbers representing nodes and tasks respective, with it assumed you want ntasks-per-node=
nodes//tasks

Then call slurm_benchmarker with a test series, the file pointing to the tuples, which program you are wishing to record, and whether or not you want the size of the problem to scale. 

Once these have all returned, call slurm_logviz with similar commands.

python slurm_benchmarker.py --test-series-name=scaledRunTwoNodes --tuples=node_tuples.txt --program=lammps --size=free 
python -i slurm_logvis.py --test-series-name=fixedRunsOneNode --program=lammps 


Note do not put senistive data like account numbers in the machine specific directives



