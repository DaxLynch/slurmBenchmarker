import subprocess
import pandas as pd
from benchmark import ensure_csv
from benchmark import open_tuple_file

#What should it take as an input??
#Should it take a test_number? Should it take the list of files?
def lammps(test_number): #results is a dictionary of results
    test_number_directory = join("benchmark_results",test_series_name)
    if not os.path.exists(test_number_directory):
        raise FileNotFoundError(f"The directory {test_number_directory} does not exist.")

    file_walk = os.walk(test_number_directory)
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
        SingleProcTime = data.at[1,"Wall Time"] #ASSUMING THERE IS A 1 NODE 1 TASK
        if args_dict["scaling"] == "fixed":
            data["Parallel Eff"] = SingleProcTime/(data["Wall Time"]*data.index)*100
        else:
            data["Parallel Eff"] = SingleProcTime/data["Wall Time"]*100
        data.to_csv(join(test_number_directory,test_series_name)+"Results.csv")
    return data 

args_dict = {}

if __name__ == "__main__":

    # Create the parser
    parser = argparse.ArgumentParser(description='Collates information from a series of test runs of a program on a slurm cluster')

    parser.add_argument('--test-number', required=True,type=str, help='Name of a series of test')
    # Parse arguments
    args = parser.parse_args()
    args_dict = vars(args)
     
    # Load the output files 
    test_number_directory = join("benchmark_results",test_number)
    if not os.path.exists(test_number_directory):
        raise FileNotFoundError(f"The directory {test_number_directory} does not exist.")

    node_file = os.join(test_number_directory,"node_tuples.txt")
    if not os.path.exists(node_file):
        raise FileNotFoundError(f"The file {node_file} does not exist.")
  
     # Load the CSV file
    csv_path = f"results.csv"
    results_df = ensure_csv(csv_path)
 
    # Load the node_tuples.txt
    for nodes, tasks in open_tuple_file(node_file):
        new_test_results = {"Test Number": test_number, "OS": "linux"} #Alter so it includes cluster type, date??, other reasonable info

        lammps_results = lammps(test_number, nodes, tasks) #THis should check for existence of the lamps file, and if it produces a naan should atleast throw a warning
        new_test_results.update(lammps_results)

        openFOAM_results = openFOAM(test_number, nodes, tasks)
        new_test_results.update(openFOAM_results)
        
        results_df.concat(new_test_results)


    # Update the .csv file
    results_df.to_csv(csv_path)

