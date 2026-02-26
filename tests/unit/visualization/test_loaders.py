"""Unit tests for visualization loaders module."""

import pytest
import pandas as pd
from pathlib import Path
from lpm_validation.visualization.loaders import (
    load_csv,
    load_dataset,
    load_multiple_datasets,
    identify_baseline_rows,
    filter_morphs_only,
    _convert_types
)


class TestLoadCSV:
    """Test load_csv function."""
    
    def test_load_csv_basic(self, sample_csv_file):
        """Test loading a single CSV file."""
        df = load_csv(sample_csv_file)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert 'Unique_ID' in df.columns
        assert 'Cd' in df.columns
        # Check that delta columns are added by default
        assert 'Cd_delta' in df.columns
        assert 'Cl_delta' in df.columns
    
    def test_load_csv_with_filters(self, sample_csv_file):
        """Test loading CSV with filters applied."""
        df = load_csv(sample_csv_file, filters={'Simulator': 'JakubNet'})
        
        assert all(df['Simulator'] == 'JakubNet')
        # Delta columns should still be added
        assert 'Cd_delta' in df.columns
    
    def test_load_csv_multiple_filters(self, sample_csv_file):
        """Test loading CSV with multiple filters."""
        df = load_csv(sample_csv_file, filters={
            'Simulator': 'JakubNet',
            'Car_Group': 'Sedan'
        })
        
        if len(df) > 0:
            assert all(df['Simulator'] == 'JakubNet')
            assert all(df['Car_Group'] == 'Sedan')
    
    def test_load_csv_invalid_column_filter(self, sample_csv_file):
        """Test that invalid filter column is handled gracefully."""
        # Should not raise error, just log warning
        df = load_csv(sample_csv_file, filters={'NonExistentColumn': 'value'})
        assert isinstance(df, pd.DataFrame)
    
    def test_load_csv_no_deltas(self, sample_csv_file):
        """Test loading CSV without delta computation."""
        df = load_csv(sample_csv_file, compute_deltas=False)
        
        assert 'Cd_delta' not in df.columns
        assert 'Cl_delta' not in df.columns
    
    def test_load_csv_custom_delta_metrics(self, sample_csv_file):
        """Test loading CSV with custom delta metrics."""
        df = load_csv(sample_csv_file, delta_metrics=['Cd', 'Drag_N'])
        
        assert 'Cd_delta' in df.columns
        assert 'Drag_N_delta' in df.columns


class TestLoadDataset:
    """Test load_dataset function."""
    
    def test_load_dataset_all_files(self, sample_csv_dir):
        """Test loading all CSV files from directory."""
        df = load_dataset(sample_csv_dir)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        # Check delta columns are added by default
        assert 'Cd_delta' in df.columns
        assert 'Cl_delta' in df.columns
    
    def test_load_dataset_filter_simulator(self, sample_csv_dir):
        """Test loading dataset filtered by simulator."""
        df = load_dataset(sample_csv_dir, simulator='JakubNet')
        
        if len(df) > 0:
            assert all(df['Simulator'] == 'JakubNet')
    
    def test_load_dataset_filter_baseline(self, sample_csv_dir):
        """Test loading dataset filtered by baseline_id."""
        df = load_dataset(sample_csv_dir, baseline_id='Car1')
        
        if len(df) > 0:
            assert all(df['Baseline_ID'] == 'Car1')
    
    def test_load_dataset_filter_car_group(self, sample_csv_dir):
        """Test loading dataset filtered by car_group."""
        df = load_dataset(sample_csv_dir, car_group='Sedan')
        
        if len(df) > 0:
            assert all(df['Car_Group'] == 'Sedan')
    
    def test_load_dataset_filter_status(self, sample_csv_dir):
        """Test loading dataset filtered by status."""
        df = load_dataset(sample_csv_dir, status='complete')
        
        if len(df) > 0:
            assert all(df['Status'] == 'complete')
    
    def test_load_dataset_empty_dir(self, tmp_path):
        """Test loading from empty directory."""
        df = load_dataset(tmp_path)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
    
    def test_load_dataset_nonexistent_dir(self):
        """Test loading from non-existent directory raises error."""
        with pytest.raises(FileNotFoundError):
            load_dataset('/nonexistent/path')
    
    def test_load_dataset_no_deltas(self, sample_csv_dir):
        """Test loading dataset without delta computation."""
        df = load_dataset(sample_csv_dir, compute_deltas=False)
        
        assert 'Cd_delta' not in df.columns
        assert 'Cl_delta' not in df.columns


class TestLoadMultipleDatasets:
    """Test load_multiple_datasets function."""
    
    def test_load_multiple_datasets_basic(self, sample_csv_dir):
        """Test loading multiple datasets with different filters."""
        configs = [
            {'directory': sample_csv_dir, 'simulator': 'JakubNet', 'label': 'JakubNet'},
            {'directory': sample_csv_dir, 'simulator': 'DES', 'label': 'DES'},
        ]
        
        datasets = load_multiple_datasets(configs)
        
        assert isinstance(datasets, list)
        assert len(datasets) <= 2  # May be less if simulators don't exist
        
        for df, label in datasets:
            assert isinstance(df, pd.DataFrame)
            assert isinstance(label, str)
    
    def test_load_multiple_datasets_with_filters(self, sample_csv_dir):
        """Test loading datasets with various filters."""
        configs = [
            {
                'directory': sample_csv_dir,
                'simulator': 'JakubNet',
                'car_group': 'Sedan',
                'label': 'JakubNet Sedans'
            },
        ]
        
        datasets = load_multiple_datasets(configs)
        
        for df, label in datasets:
            if len(df) > 0:
                assert all(df['Simulator'] == 'JakubNet')
                assert all(df['Car_Group'] == 'Sedan')
    
    def test_load_multiple_datasets_missing_directory(self):
        """Test handling of config missing directory field."""
        configs = [
            {'label': 'Test'},  # Missing 'directory'
        ]
        
        datasets = load_multiple_datasets(configs)
        
        assert len(datasets) == 0


class TestFilterMorphsOnly:
    """Test filter_morphs_only function."""
    
    def test_filter_morphs_only(self, sample_dataframe_with_morphs):
        """Test filtering to only morph geometries."""
        morphs = filter_morphs_only(sample_dataframe_with_morphs)
        
        # All returned rows should have non-empty Morph_Type
        for _, row in morphs.iterrows():
            morph = row['Morph_Type']
            assert pd.notna(morph) and morph != ''
    
    def test_filter_morphs_only_count(self, sample_dataframe_with_morphs):
        """Test correct number of morph rows identified."""
        morphs = filter_morphs_only(sample_dataframe_with_morphs)
        baselines = identify_baseline_rows(sample_dataframe_with_morphs)
        
        # Morphs + baselines should equal total rows
        assert len(morphs) + len(baselines) == len(sample_dataframe_with_morphs)


class TestIdentifyBaselineRows:
    """Test identify_baseline_rows function."""
    
    def test_identify_baseline_rows(self, sample_dataframe):
        """Test identifying baseline rows."""
        baselines = identify_baseline_rows(sample_dataframe)
        
        # All returned rows should have empty/None Morph_Type
        for _, row in baselines.iterrows():
            morph = row['Morph_Type']
            assert pd.isna(morph) or morph == ''
    
    def test_identify_baseline_rows_count(self, sample_dataframe_with_morphs):
        """Test correct number of baseline rows identified."""
        baselines = identify_baseline_rows(sample_dataframe_with_morphs)
        
        # Should have fewer rows than original (only baselines)
        assert len(baselines) < len(sample_dataframe_with_morphs)


class TestConvertTypes:
    """Test _convert_types function."""
    
    def test_convert_float_columns(self):
        """Test conversion of float columns."""
        df = pd.DataFrame({
            'Cd': ['0.25', '0.26'],
            'Cl': ['0.10', '0.11'],
            'Morph_Value': ['10.0', '20.0']
        })
        
        df_converted = _convert_types(df)
        
        assert df_converted['Cd'].dtype == float
        assert df_converted['Cl'].dtype == float
        assert df_converted['Morph_Value'].dtype == float
    
    def test_convert_boolean_columns(self):
        """Test conversion of boolean columns."""
        df = pd.DataFrame({
            'Has_Results': ['True', 'False'],
            'Converged': [True, False]
        })
        
        df_converted = _convert_types(df)
        
        assert df_converted['Has_Results'].dtype == bool
        assert df_converted['Converged'].dtype == bool
    
    def test_convert_handles_na_values(self):
        """Test handling of NA/empty values."""
        df = pd.DataFrame({
            'Cd': ['0.25', '', 'invalid'],
            'Has_Results': ['True', '', 'False']
        })
        
        df_converted = _convert_types(df)
        
        # Should not raise error, NaN for invalid float
        assert pd.isna(df_converted['Cd'].iloc[1])
        assert pd.isna(df_converted['Cd'].iloc[2])
