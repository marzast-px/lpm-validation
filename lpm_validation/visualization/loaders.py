"""Data loading utilities for CSV validation data."""

import logging
from pathlib import Path
from typing import Optional, Dict, List, Union, Tuple
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def load_csv(
    filepath: Union[str, Path],
    filters: Optional[Dict[str, str]] = None,
    compute_deltas: bool = True,
    delta_metrics: Optional[List[str]] = None
) -> pd.DataFrame:
    """Load a single CSV file with optional filtering and automatic delta calculation.
    
    Args:
        filepath: Path to CSV file
        filters: Optional dict of column:value pairs to filter by
                Example: {'Simulator': 'DES', 'Car_Group': 'Sedan'}
        compute_deltas: Whether to automatically compute delta columns (default: True)
        delta_metrics: Metrics to compute deltas for (default: ['Cd', 'Cl'])
    
    Returns:
        DataFrame with loaded and filtered data, including delta columns
    
    Example:
        >>> df = load_csv('output/JakubNet_AudiA4.csv')
        >>> df_des = load_csv('output/all_results.csv', filters={'Simulator': 'DES'})
        >>> df_no_deltas = load_csv('output/data.csv', compute_deltas=False)
    """
    logger.info(f"Loading CSV from {filepath}")
    
    # Load CSV
    df = pd.read_csv(filepath)
    
    # Convert data types
    df = _convert_types(df)
    
    # Apply filters
    if filters:
        for column, value in filters.items():
            if column in df.columns:
                df = df[df[column] == value]
                logger.debug(f"Filtered by {column}={value}, {len(df)} rows remaining")
            else:
                logger.warning(f"Filter column '{column}' not found in CSV")
    
    # Compute deltas if requested
    if compute_deltas:
        df = _add_delta_columns(df, metrics=delta_metrics)
    
    logger.info(f"Loaded {len(df)} rows from {filepath}")
    return df


def load_dataset(
    directory: Union[str, Path],
    simulator: Optional[str] = None,
    baseline_id: Optional[str] = None,
    car_group: Optional[str] = None,
    status: Optional[str] = None,
    compute_deltas: bool = True,
    delta_metrics: Optional[List[str]] = None
) -> pd.DataFrame:
    """Load all matching CSV files from a directory with automatic delta calculation.
    
    Args:
        directory: Path to directory containing CSV files
        simulator: Filter by simulator name (e.g., 'JakubNet', 'DES')
        baseline_id: Filter by baseline car name (e.g., 'Audi_RS7')
        car_group: Filter by car group (e.g., 'Sedan', 'SUV')
        status: Filter by status ('complete', 'complete_not_converged', 'incomplete')
        compute_deltas: Whether to automatically compute delta columns (default: True)
        delta_metrics: Metrics to compute deltas for (default: ['Cd', 'Cl'])
    
    Returns:
        Combined DataFrame with all matching data, including delta columns
    
    Example:
        >>> # Load all DES results
        >>> df_des = load_dataset('./output', simulator='DES')
        >>> # Load all simulators for one car
        >>> df_audi = load_dataset('./output', baseline_id='Audi_RS7')
        >>> # Load specific car group with custom delta metrics
        >>> df_sedans = load_dataset('./output', car_group='Sedan', delta_metrics=['Cd', 'Cl', 'Avg_Cd'])
    """
    directory = Path(directory)
    
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    logger.info(f"Loading datasets from {directory}")
    
    # Find all CSV files
    csv_files = list(directory.glob("*.csv"))
    
    if not csv_files:
        logger.warning(f"No CSV files found in {directory}")
        return pd.DataFrame()
    
    logger.info(f"Found {len(csv_files)} CSV files")
    
    # Load and combine all CSVs
    dataframes = []
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            df = _convert_types(df)
            dataframes.append(df)
        except Exception as e:
            logger.error(f"Error loading {csv_file}: {e}")
    
    if not dataframes:
        return pd.DataFrame()
    
    # Combine all dataframes
    combined_df = pd.concat(dataframes, ignore_index=True)
    logger.info(f"Combined {len(dataframes)} files into {len(combined_df)} rows")
    
    # Apply filters
    if simulator:
        combined_df = combined_df[combined_df['Simulator'] == simulator]
        logger.info(f"Filtered by Simulator={simulator}, {len(combined_df)} rows remaining")
    
    if baseline_id:
        combined_df = combined_df[combined_df['Baseline_ID'] == baseline_id]
        logger.info(f"Filtered by Baseline_ID={baseline_id}, {len(combined_df)} rows remaining")
    
    if car_group:
        combined_df = combined_df[combined_df['Car_Group'] == car_group]
        logger.info(f"Filtered by Car_Group={car_group}, {len(combined_df)} rows remaining")
    
    if status:
        combined_df = combined_df[combined_df['Status'] == status]
        logger.info(f"Filtered by Status={status}, {len(combined_df)} rows remaining")
    
    # Compute deltas if requested
    if compute_deltas:
        combined_df = _add_delta_columns(combined_df, metrics=delta_metrics)
    
    return combined_df


def load_multiple_datasets(
    configs: List[Dict],
    compute_deltas: bool = True,
    delta_metrics: Optional[List[str]] = None
) -> List[Tuple[pd.DataFrame, str]]:
    """Load multiple datasets with different filters and labels.
    
    Args:
        configs: List of configuration dicts, each containing:
                - 'directory': Path to CSV directory
                - 'label': Label for this dataset
                - Optional filters: 'simulator', 'baseline_id', 'car_group', 'status'
        compute_deltas: Whether to automatically compute delta columns (default: True)
        delta_metrics: Metrics to compute deltas for (default: ['Cd', 'Cl'])
    
    Returns:
        List of (DataFrame, label) tuples
    
    Example:
        >>> configs = [
        ...     {'directory': './output', 'simulator': 'JakubNet', 'label': 'JakubNet'},
        ...     {'directory': './output', 'simulator': 'DES', 'label': 'DES'},
        ... ]
        >>> datasets = load_multiple_datasets(configs)
        >>> for df, label in datasets:
        ...     print(f"{label}: {len(df)} rows")
    """
    datasets = []
    
    for config in configs:
        directory = config.get('directory')
        label = config.get('label', 'Unnamed Dataset')
        
        if not directory:
            logger.error(f"Config missing 'directory' field: {config}")
            continue
        
        # Extract filter parameters
        filter_params = {
            'simulator': config.get('simulator'),
            'baseline_id': config.get('baseline_id'),
            'car_group': config.get('car_group'),
            'status': config.get('status'),
        }
        # Remove None values
        filter_params = {k: v for k, v in filter_params.items() if v is not None}
        
        try:
            df = load_dataset(
                directory,
                **filter_params,
                compute_deltas=compute_deltas,
                delta_metrics=delta_metrics
            )
            datasets.append((df, label))
            logger.info(f"Loaded dataset '{label}': {len(df)} rows")
        except Exception as e:
            logger.error(f"Error loading dataset '{label}': {e}")
    
    return datasets


def identify_baseline_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Return only baseline rows (where Morph_Type is empty/None).
    
    Args:
        df: Input DataFrame
    
    Returns:
        DataFrame containing only baseline rows
    
    Example:
        >>> baselines = identify_baseline_rows(df)
        >>> print(f"Found {len(baselines)} baseline geometries")
    """
    # Baseline rows have empty/null Morph_Type
    mask = df['Morph_Type'].isna() | (df['Morph_Type'] == '')
    return df[mask].copy()


def filter_morphs_only(df: pd.DataFrame) -> pd.DataFrame:
    """Return only non-baseline rows (morph geometries).
    
    Args:
        df: Input DataFrame
    
    Returns:
        DataFrame with only morph geometries (Morph_Type not None/empty)
    
    Example:
        >>> morphs_df = filter_morphs_only(df)
        >>> print(f"Found {len(morphs_df)} morph geometries")
    """
    mask = ~(df['Morph_Type'].isna() | (df['Morph_Type'] == ''))
    return df[mask].copy()


def filter_converged_results(
    datasets: Dict[str, pd.DataFrame],
    verbose: bool = True
) -> Dict[str, pd.DataFrame]:
    """Filter datasets to keep only converged simulation results.
    
    Args:
        datasets: Dictionary of DataFrames keyed by dataset name
        verbose: Print filtering statistics (default: True)
    
    Returns:
        Dictionary with same keys but filtered DataFrames containing only converged results
    
    Example:
        >>> datasets_filtered = filter_converged_results(datasets)
        >>> # Use with verbose=False to suppress output
        >>> datasets_filtered = filter_converged_results(datasets, verbose=False)
    """
    if verbose:
        print("Filtering datasets for converged results only...")
    
    datasets_filtered = {}
    
    for key, df in datasets.items():
        if df is None or len(df) == 0:
            if verbose:
                print(f"⚠ {key}: Empty dataset, skipping")
            datasets_filtered[key] = df
            continue
        
        # Check if Converged column exists
        if 'Converged' not in df.columns:
            if verbose:
                print(f"⚠ {key}: No 'Converged' column found, keeping all data")
            datasets_filtered[key] = df
            continue
        
        # Filter for converged results (Converged == True)
        df_converged = df[df['Converged'] == True].copy()
        
        original_count = len(df)
        converged_count = len(df_converged)
        removed_count = original_count - converged_count
        
        if verbose:
            if removed_count > 0:
                print(f"✓ {key}: Kept {converged_count}/{original_count} rows (removed {removed_count} non-converged)")
            else:
                print(f"✓ {key}: All {original_count} rows converged")
        
        datasets_filtered[key] = df_converged
    
    if verbose:
        print(f"\n✓ Filtering complete. Datasets ready for visualization.")
    
    return datasets_filtered


def _convert_types(df: pd.DataFrame) -> pd.DataFrame:
    """Convert CSV column types to appropriate dtypes.
    
    Args:
        df: Input DataFrame
    
    Returns:
        DataFrame with converted types
    """
    # Float columns (coefficients and forces)
    float_columns = [
        'Cd', 'Cl', 'Drag_N', 'Lift_N',
        'Avg_Cd', 'Avg_Cl', 'Avg_Drag_N', 'Avg_Lift_N',
        'Morph_Value'
    ]
    
    for col in float_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Boolean columns
    bool_columns = ['Has_Results', 'Converged']
    
    for col in bool_columns:
        if col in df.columns:
            # Handle various boolean representations
            df[col] = df[col].map({
                'True': True, 'true': True, 'TRUE': True, True: True, '1': True, 1: True,
                'False': False, 'false': False, 'FALSE': False, False: False, '0': False, 0: False,
            })
    
    return df


def _add_delta_columns(
    df: pd.DataFrame,
    metrics: Optional[List[str]] = None,
    suffix: str = '_delta'
) -> pd.DataFrame:
    """Add delta columns for specified metrics.
    
    Internal helper that calculates deltas from baseline values for morph geometries.
    
    Args:
        df: Input DataFrame
        metrics: List of metric column names (default: ['Cd', 'Cl'])
        suffix: Suffix for delta columns (default: '_delta')
    
    Returns:
        DataFrame with added delta columns
    """
    if metrics is None:
        metrics = ['Cd', 'Cl']
    
    if df.empty:
        return df
    
    df_result = df.copy()
    
    # Build baseline cache for performance
    baseline_cache = {}
    baseline_mask = df_result['Morph_Type'].isna() | (df_result['Morph_Type'] == '')
    baseline_rows = df_result[baseline_mask]
    
    for _, baseline_row in baseline_rows.iterrows():
        baseline_id = baseline_row['Baseline_ID']
        for metric in metrics:
            if metric in baseline_row:
                cache_key = (baseline_id, metric)
                baseline_cache[cache_key] = baseline_row[metric]
    
    # Add delta columns
    for metric in metrics:
        if metric not in df_result.columns:
            logger.warning(f"Metric column '{metric}' not found in DataFrame")
            continue
        
        delta_col = f"{metric}{suffix}"
        df_result[delta_col] = df_result.apply(
            lambda row: _calculate_single_delta(row, metric, baseline_cache),
            axis=1
        )
        logger.info(f"Added {delta_col} column")
    
    return df_result


def _calculate_single_delta(
    row: pd.Series,
    metric: str,
    baseline_cache: Dict[Tuple[str, str], float]
) -> Optional[float]:
    """Calculate delta for a single row.
    
    Args:
        row: DataFrame row
        metric: Metric column name
        baseline_cache: Cache of baseline values {(baseline_id, metric): value}
    
    Returns:
        Delta value (morph - baseline), or 0.0 for baseline rows, or NaN if unavailable
    """
    # If this is a baseline row, delta is 0
    if pd.isna(row['Morph_Type']) or row['Morph_Type'] == '':
        return 0.0
    
    # Get baseline value from cache
    cache_key = (row['Baseline_ID'], metric)
    baseline_value = baseline_cache.get(cache_key)
    
    if baseline_value is None or pd.isna(baseline_value):
        return np.nan
    
    # Get current value
    current_value = row[metric]
    
    if pd.isna(current_value):
        return np.nan
    
    # Calculate delta
    return current_value - baseline_value
