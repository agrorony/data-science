"""
Bus Route Analysis Module with Functions
This module provides functions to analyze bus route sequences and visualize patterns.
"""

import pandas as pd
import pathlib
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def load_and_clean_data(file_path):
    """
    Load CSV file and clean data by removing NaN values and duplicates.
    
    Args:
        file_path (str or Path): Path to the CSV file
        
    Returns:
        pd.DataFrame: Cleaned dataframe
    """
    df = pd.read_csv(file_path)
    
    # Remove rows with NaN in route_name
    df = df.dropna(subset=['route_name'])
    
    # Find and remove duplicate rows
    duplicates = df[df.duplicated()]
    print(f"Number of duplicate rows: {len(duplicates)}")
    df = df.drop_duplicates()
    
    return df


def sort_and_analyze_data(df):
    """
    Sort dataframe and analyze route blocks.
    
    Args:
        df (pd.DataFrame): Input dataframe
        
    Returns:
        tuple: (sorted_df, route_blocks, block_size)
    """
    df_sorted = df.sort_values(['route_id', 'month', 'day_of_week', 'scheduled_departure_time', 'stop_sequence'])
    
    route_blocks = df_sorted.groupby(['route_id', 'month', 'day_of_week', 'scheduled_departure_time'])
    block_size = route_blocks.size().reset_index(name='n_stops')
    
    return df_sorted, route_blocks, block_size


def extract_route_sequences(route_blocks):
    """
    Extract route sequences from grouped data.
    
    Args:
        route_blocks: Grouped dataframe
        
    Returns:
        pd.DataFrame: Route sequences with counts and number of stops
    """
    def get_route_sequence(group):
        return group.sort_values('stop_sequence')['stop_code'].tolist()
    
    route_sequences = route_blocks.apply(get_route_sequence).reset_index()
    route_sequences = route_sequences.rename(columns={0: 'route_sequence'})
    
    # Convert to string format
    route_sequences['route_sequence_str'] = route_sequences['route_sequence'].apply(
        lambda x: '-'.join(map(str, x))
    )
    
    # Count occurrences
    route_counts = route_sequences['route_sequence_str'].value_counts().reset_index()
    route_counts = route_counts.rename(columns={'route_sequence_str': 'count', 'index': 'route_sequence_str'})
    
    # Add number of stops column
    route_counts['n_stops'] = route_counts['route_sequence_str'].apply(lambda x: len(x.split('-')))
    
    return route_sequences, route_counts


def get_most_common_route(route_counts):
    """
    Get the most common route sequence.
    
    Args:
        route_counts (pd.DataFrame): Route counts dataframe
        
    Returns:
        tuple: (most_common_route_str, most_common_route_list)
    """
    most_common_route_str = route_counts.iloc[0]['route_sequence_str']
    most_common_route = most_common_route_str.split('-')
    
    return most_common_route_str, most_common_route


def filter_and_classify_routes(route_counts, most_common_route_str):
    """
    Filter routes and classify by number of stops.
    
    Args:
        route_counts (pd.DataFrame): Route counts dataframe
        most_common_route_str (str): The most common route sequence
        
    Returns:
        tuple: (other_routes_sorted, stops_distribution)
    """
    # Remove the most common route
    other_routes = route_counts[route_counts['route_sequence_str'] != most_common_route_str]
    
    # Sort by number of stops and count
    other_routes_sorted = other_routes.sort_values(by=['n_stops', 'count'])
    
    # Get distribution of stops
    stops_distribution = other_routes_sorted.groupby('n_stops').size().reset_index(name='n_routes')
    stops_distribution = stops_distribution.sort_values(by='n_stops')
    
    return other_routes_sorted, stops_distribution


def load_stops_mapping(stops_file):
    """
    Load stops information and create mapping from code to name.
    
    Args:
        stops_file (str or Path): Path to stops CSV file
        
    Returns:
        dict: Mapping from stop code to stop name
    """
    stops_df = pd.read_csv(stops_file)
    stop_code_to_name = dict(zip(stops_df['stop_code'], stops_df['stop_name']))
    return stop_code_to_name


def get_stop_names(stop_codes, stop_code_to_name):
    """
    Convert stop codes string to list of stop names.
    
    Args:
        stop_codes (str): Stop codes as string separated by '-'
        stop_code_to_name (dict): Mapping from code to name
        
    Returns:
        list: List of stop names
    """
    codes = stop_codes.split('-')
    names = [stop_code_to_name.get(int(code), f"Unknown({code})") for code in codes]
    return names


def plot_rare_routes(other_routes_sorted):
    """
    Plot scatter plot of rare routes (stops vs occurrences).
    
    Args:
        other_routes_sorted (pd.DataFrame): Sorted routes dataframe
    """
    plt.figure(figsize=(10, 6))
    plt.scatter(other_routes_sorted['n_stops'], other_routes_sorted['count'], alpha=0.7)
    plt.xlabel('Number of stops in route')
    plt.ylabel('Number of occurrences')
    plt.title('Rare route sequences: number of stops vs occurrences')
    plt.grid(True)
    plt.show()


def filter_by_stop_count(other_routes_sorted, min_stops=10, max_stops=50):
    """
    Filter routes by number of stops.
    
    Args:
        other_routes_sorted (pd.DataFrame): Sorted routes dataframe
        min_stops (int): Minimum number of stops
        max_stops (int): Maximum number of stops
        
    Returns:
        pd.DataFrame: Filtered routes
    """
    filtered_routes = other_routes_sorted[
        (other_routes_sorted['n_stops'] >= min_stops) & 
        (other_routes_sorted['n_stops'] <= max_stops)
    ]
    print(f"Number of routes after filtering ({min_stops}-{max_stops} stops): {len(filtered_routes)}")
    return filtered_routes


def create_heatmap_data(subset_routes, reference_stations, stop_code_to_name):
    """
    Create heatmap data showing which reference stations appear in each route.
    
    Args:
        subset_routes (pd.DataFrame): Routes subset to analyze
        reference_stations (list): Reference station names
        stop_code_to_name (dict): Stop code to name mapping
        
    Returns:
        tuple: (heatmap_data, labels_y)
    """
    heatmap_data = []
    labels_y = []
    
    for idx, row in subset_routes.iterrows():
        # Extract stops of current route
        current_route_stops = set(get_stop_names(row['route_sequence_str'], stop_code_to_name))
        
        # Build vector: 1 if stop from reference is in current route, 0 otherwise
        vector = [1 if stop in current_route_stops else 0 for stop in reference_stations]
        
        heatmap_data.append(vector)
        labels_y.append(f"Route {idx}")
    
    heatmap_data = np.array(heatmap_data)
    return heatmap_data, labels_y


def plot_routes_heatmap(heatmap_data, reference_stations, labels_y, bin_label):
    """
    Plot heatmap showing route coverage.
    
    Args:
        heatmap_data (np.ndarray): 2D array of heatmap data
        reference_stations (list): Reference station names
        labels_y (list): Labels for y-axis (routes)
        bin_label (str): Label describing the bin (e.g., "10-20")
    """
    # Reverse station labels for RTL display (if needed)
    station_labels_rtl = reference_stations  # Remove reversal if not needed
    
    plt.figure(figsize=(14, 6))
    sns.heatmap(heatmap_data, annot=False, cbar=False, cmap='YlGnBu',
                xticklabels=station_labels_rtl, yticklabels=labels_y,
                linecolor='black', linewidths=0.5)
    
    plt.xticks(rotation=45, ha='right')
    plt.title(f"Heatmap for routes with {bin_label} stops (0=absent, 1=present)")
    plt.ylabel("Route Index")
    plt.xlabel("Stations (in most common route order)")
    plt.tight_layout()
    plt.show()


def analyze_routes_by_stop_count(filtered_routes, route_counts, most_common_route_str,
                                  reference_stations, stop_code_to_name,
                                  bins=None, bin_labels=None):
    """
    Analyze and visualize routes grouped by stop count ranges.
    
    Args:
        filtered_routes (pd.DataFrame): Filtered routes dataframe
        route_counts (pd.DataFrame): All route counts
        most_common_route_str (str): Most common route sequence
        reference_stations (list): Reference station names
        stop_code_to_name (dict): Stop code to name mapping
        bins (list): Stop count bin boundaries
        bin_labels (list): Labels for each bin
    """
    if bins is None:
        bins = [10, 20, 30, 40, 50]
    if bin_labels is None:
        bin_labels = ["10-20", "20-30", "30-40", "40-50"]
    
    # Get the most common route
    most_common_df = route_counts[route_counts['route_sequence_str'] == most_common_route_str]
    
    for i in range(len(bins) - 1):
        low = bins[i]
        high = bins[i + 1]
        
        # Filter routes in current range
        subset = filtered_routes[(filtered_routes['n_stops'] > low) & (filtered_routes['n_stops'] <= high)]
        if subset.empty:
            continue
        
        # Concat with most common route
        subset_routes = pd.concat([most_common_df, subset])
        
        # Create heatmap data
        heatmap_data, labels_y = create_heatmap_data(subset_routes, reference_stations, stop_code_to_name)
        
        # Plot heatmap
        plot_routes_heatmap(heatmap_data, reference_stations, labels_y, bin_labels[i])


def full_analysis_pipeline(file_path, stops_file):
    """
    Run complete analysis pipeline.
    
    Args:
        file_path (str or Path): Path to ride data CSV
        stops_file (str or Path): Path to stops CSV
    """
    print("Loading and cleaning data...")
    df = load_and_clean_data(file_path)
    
    print("Sorting and analyzing routes...")
    df_sorted, route_blocks, block_size = sort_and_analyze_data(df)
    
    print("Extracting route sequences...")
    route_sequences, route_counts = extract_route_sequences(route_blocks)
    
    print(f"Total unique route sequences: {route_counts.shape[0]}")
    print(f"Most common route has {route_counts.iloc[0]['n_stops']} stops")
    
    print("Getting most common route...")
    most_common_route_str, most_common_route = get_most_common_route(route_counts)
    
    print("Filtering and classifying routes...")
    other_routes_sorted, stops_distribution = filter_and_classify_routes(route_counts, most_common_route_str)
    
    print("Plotting rare routes scatter...")
    plot_rare_routes(other_routes_sorted)
    
    print("Filtering by stop count...")
    filtered_routes = filter_by_stop_count(other_routes_sorted, min_stops=10, max_stops=50)
    
    print("Loading stops mapping...")
    stop_code_to_name = load_stops_mapping(stops_file)
    
    print("Preparing reference stations...")
    reference_stations = get_stop_names(most_common_route_str, stop_code_to_name)
    
    print("Creating visualizations...")
    analyze_routes_by_stop_count(filtered_routes, route_counts, most_common_route_str,
                                  reference_stations, stop_code_to_name)
    
    print("Analysis complete!")


# Example usage
if __name__ == "__main__":
    # Set paths
    ride_data_path = r"C:\Users\User\Documents\שנה ג\data_science\data-science\govData\renamed_ride_data_15.csv"
    stops_data_path = r"C:\Users\User\Documents\שנה ג\data_science\data-science\govData\jerusalem_stops.csv"
    
    # Run analysis
    full_analysis_pipeline(ride_data_path, stops_data_path)
