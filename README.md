This Repo is meant to aid me in benchmarking various programs that run on slurm, with the goal of comparing performance across multiple HPC systems.

It uses the node_tuples.txt to submit multiple slurm sbatch scripts with varying node and task sizes, so you can see how performance scales with inter- and intranode communication. It then uploads the results into results.csv.
To run, alter the node_tuples.txt to show how many runs you want of specfic sizes, the two numbers representing nodes and tasks respective, with it assumed you want ntasks-per-node=nodes//tasks

If running on perlmutter cluster, alter the below line:
#SBATCH -A ###CHANGE ME TO YOUR PERLMUTTER ACCOUNT NUMBER###

Then call benchmarker.py with the provider and instance type. Once these have all returned, call upload.py with the test number of the data you want to upload.

for example:
git pull (loads the most recent results.csv)
python benchmark.py  --provider=aws --instance-type=g4dn.8xlarge
python update.py  --test-number=1738562555
git add results.csv
git push
