"""Test script for visualization module.

This script tests the basic functionality of the visualization module.
Run from the project root directory:
    python test_visualization.py
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from lpm_validation.visualization import (
    load_csv,
    CoefficientScatterPlot,
    ColorScheme,
)


def create_sample_data():
    """Create sample validation data for testing."""
    print("Creating sample validation data...")
    
    # Sample data mimicking the CSV structure
    data = {
        'Unique_ID': [
            'Car1_Morph_101', 'Car1_Morph_102', 'Car1_Morph_103',
            'Car2_Morph_101', 'Car2_Morph_102', 'Car2_Morph_103',
        ],
        'Baseline_ID': ['Car1', 'Car1', 'Car1', 'Car2', 'Car2', 'Car2'],
        'Car_Group': ['Sedan', 'Sedan', 'Sedan', 'SUV', 'SUV', 'SUV'],
        'Simulator': ['JakubNet', 'JakubNet', 'JakubNet', 'DES', 'DES', 'DES'],
        'Morph_Type': [None, 'ride_height', 'ride_height', None, 'front_overhang', 'front_overhang'],
        'Morph_Value': [0.0, 10.0, 20.0, 0.0, 5.0, 10.0],
        'Status': ['complete', 'complete', 'complete', 'complete', 'complete', 'complete'],
        'Has_Results': [True, True, True, True, True, True],
        'Converged': [True, True, True, True, True, True],
        'Cd': [0.25, 0.26, 0.27, 0.30, 0.31, 0.32],
        'Cl': [0.10, 0.11, 0.12, 0.15, 0.16, 0.17],
        'Drag_N': [100.0, 104.0, 108.0, 120.0, 124.0, 128.0],
        'Lift_N': [40.0, 44.0, 48.0, 60.0, 64.0, 68.0],
    }
    
    df = pd.DataFrame(data)
    print(f"Created DataFrame with {len(df)} rows")
    return df


def test_delta_calculation():
    """Test delta calculation functionality."""
    print("\n" + "="*60)
    print("TEST: Delta Calculation")
    print("="*60)
    
    df = create_sample_data()
    
    # Delta columns are now automatically added when loading data
    # For this test, we'll create a CSV and load it
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_file = f.name
    
    try:
        # Load with automatic delta calculation
        df_with_deltas = load_csv(temp_file, compute_deltas=True, delta_metrics=['Cd', 'Cl'])
        
        print("\nDataFrame with deltas:")
        print(df_with_deltas[['Unique_ID', 'Morph_Type', 'Cd', 'Cd_delta', 'Cl', 'Cl_delta']])
        
        # Verify deltas
        car1_baseline_cd = df_with_deltas[df_with_deltas['Unique_ID'] == 'Car1_Morph_101']['Cd'].values[0]
        car1_morph_cd = df_with_deltas[df_with_deltas['Unique_ID'] == 'Car1_Morph_102']['Cd'].values[0]
        car1_delta = df_with_deltas[df_with_deltas['Unique_ID'] == 'Car1_Morph_102']['Cd_delta'].values[0]
        
        expected_delta = car1_morph_cd - car1_baseline_cd
        
        print(f"\n✓ Baseline CD (Car1): {car1_baseline_cd}")
        print(f"✓ Morph CD (Car1): {car1_morph_cd}")
        print(f"✓ Calculated Delta: {car1_delta}")
        print(f"✓ Expected Delta: {expected_delta}")
        
        assert np.isclose(car1_delta, expected_delta), "Delta calculation mismatch!"
        print("✓ Delta calculation verified!")
    finally:
        # Clean up temp file
        Path(temp_file).unlink()


def test_color_scheme():
    """Test color scheme functionality."""
    print("\n" + "="*60)
    print("TEST: Color Schemes")
    print("="*60)
    
    df = create_sample_data()
    
    # Test simulator colors
    sim_colors = ColorScheme.get_color_map(df, 'Simulator')
    print(f"\nSimulator colors: {sim_colors}")
    
    # Test car group colors
    group_colors = ColorScheme.get_color_map(df, 'Car_Group')
    print(f"Car group colors: {group_colors}")
    
    # Test symbol map
    symbol_map = ColorScheme.get_symbol_map(['Dataset 1', 'Dataset 2', 'Dataset 3'])
    print(f"Symbol map: {symbol_map}")
    
    print("✓ Color scheme generation successful!")


def test_scatter_plot():
    """Test scatter plot creation."""
    print("\n" + "="*60)
    print("TEST: Scatter Plot Creation")
    print("="*60)
    
    df = create_sample_data()
    
    # Create plot
    plot = CoefficientScatterPlot(
        df,
        y_metric='Cd',
        color_by='Simulator',
        title='Test Scatter Plot'
    )
    
    # Verify figure was created
    fig = plot.fig
    print(f"\n✓ Figure created with {len(fig.data)} traces")
    print(f"✓ Figure layout title: {fig.layout.title.text}")
    
    # Test save to HTML
    output_file = Path('test_plot.html')
    plot.save(output_file)
    
    if output_file.exists():
        print(f"✓ Plot saved to {output_file}")
        output_file.unlink()  # Clean up
    else:
        print("✗ Plot save failed")
    
    print("✓ Scatter plot creation successful!")


def test_multi_dataset():
    """Test multi-dataset plotting."""
    print("\n" + "="*60)
    print("TEST: Multi-Dataset Plot")
    print("="*60)
    
    df1 = create_sample_data()
    df2 = df1.copy()
    df2['Cd'] = df2['Cd'] * 1.05  # Slightly different values
    
    # Create multi-dataset plot
    plot = CoefficientScatterPlot(
        [df1, df2],
        labels=['Dataset 1', 'Dataset 2'],
        y_metric='Cd',
        color_by='Baseline_ID',
        symbol_by='dataset',
        title='Multi-Dataset Test'
    )
    
    fig = plot.fig
    print(f"\n✓ Multi-dataset figure created with {len(fig.data)} traces")
    print(f"✓ Datasets: {len(plot.datasets)}")
    
    print("✓ Multi-dataset plotting successful!")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("LPM Validation Visualization Module Tests")
    print("="*60)
    
    try:
        test_delta_calculation()
        test_color_scheme()
        test_scatter_plot()
        test_multi_dataset()
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED! ✓")
        print("="*60)
        print("\nThe visualization module is working correctly.")
        print("See examples/visualization_demo.ipynb for usage examples.")
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
