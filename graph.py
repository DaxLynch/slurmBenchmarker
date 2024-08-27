import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

def plot_performance_over_time(provider, instance_type):
    # Load the data
    df = pd.read_csv('results.csv')

    # Filter the DataFrame based on provider, instance type, nodes, and tasks
    filtered_df = df[(df['Provider'] == provider) & 
                     (df['Instance Type'] == instance_type) & 
                     (df['Nodes'] == 4) & 
                     (df['Tasks'] == 64)]

    # Convert 'Test Number' to datetime
    filtered_df['Date'] = filtered_df['Test Number'].apply(lambda x: datetime.fromtimestamp(x))

    # Initialize the plot
    plt.figure(figsize=(12, 6))

    # Plot each program's PE over time
    programs = ['Lammps PE', 'openFOAM PE', 'Nekbone PE', 'QuanEspress PE', 'Xyce PE']
    for program in programs:
        plt.plot(filtered_df['Date'], filtered_df[program], label=program)

    # Customize the plot
    plt.title(f'Performance Over Time for {provider} {instance_type}')
    plt.xlabel('Date')
    plt.ylabel('Parallel Efficiency (PE)')
    plt.ylim(0, 100)
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)

    # Save the plot
    plt.savefig(f'performance_over_time_{provider}_{instance_type}.png')

    # Show the plot
    plt.show()

def plot_performance_across_providers(file_path):
    # Load the data
    df = pd.read_csv(file_path)

    # Filter DataFrame for the relevant node and task configuration
    filtered_df = df[(df['Nodes'] == 4) & (df['Tasks'] == 64)]

    # Get the unique providers
    providers = filtered_df['Provider'].unique()

    # Prepare the plot
    plt.figure(figsize=(12, 6))

    # Programs to plot
    programs = ['Lammps PE', 'openFOAM PE', 'Nekbone PE', 'QuanEspress PE', 'Xyce PE']

    # Loop through each provider
    for provider in providers:
        # Filter data for the current provider
        provider_df = filtered_df[filtered_df['Provider'] == provider]

        # Get unique instance types and sort by 'Test Number' in descending order
        instance_types = provider_df['Instance Type'].unique()
        latest_instances = []

        # Select the latest up to two instance types
        for instance_type in instance_types:
            instance_df = provider_df[provider_df['Instance Type'] == instance_type]
            latest_test = instance_df.loc[instance_df['Test Number'].idxmax()]
            latest_instances.append(latest_test)

        # Sort by 'Test Number' in descending order to get the two most recent results
        latest_instances.sort(key=lambda x: x['Test Number'], reverse=True)
        latest_instances = latest_instances[:2]  # Keep only up to two instance types

        # Plot each instance type for the current provider
        for instance in latest_instances:
            instance_label = f"{instance['Provider']} {instance['Instance Type']}"
            plt.plot(programs, [instance[program] for program in programs], marker='o', label=instance_label)

    # Customize the plot
    plt.title('Performance Comparison Across Providers and Instance Types')
    plt.xlabel('Programs')
    plt.ylabel('Parallel Efficiency (PE)')
    plt.ylim(0, 100)
    plt.legend()
    plt.grid(True)

    # Save the plot
    plt.savefig('performance_across_providers.png')

    # Show the plot
    plt.show()

# Example call to the function
plot_performance_across_providers('results.csv')

# Example call to the function
#plot_performance_over_time('aws', 'g4dn.8xlarge')
