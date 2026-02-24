"""Unit tests for results_extractor module."""

import pytest
import numpy as np
from unittest.mock import Mock
from lpm_validation.results_extractor import ResultsExtractor


class TestResultsExtractor:
    """Test ResultsExtractor class."""
    
    def test_extract_simulation_results(self, sample_results_json):
        """Test the main public method for extracting simulation results."""
        import csv
        from pathlib import Path
        
        mock_data_source = Mock()
        
        # Mock reading export_scalars.json
        mock_data_source.read_json.return_value = sample_results_json
        
        # Mock reading export_force_series.csv (return empty for simplicity)
        mock_data_source.read_csv.return_value = None
        
        extractor = ResultsExtractor(mock_data_source)
        
        result = extractor.extract_simulation_results(
            "test/results/Audi_RS7_Sportback_Symmetric_Morph_101",
            simulator="JakubNet"
        )
        
        # Verify JSON was read from correct path
        mock_data_source.read_json.assert_called_once_with(
            "test/results/Audi_RS7_Sportback_Symmetric_Morph_101/export_scalars.json"
        )
        
        # Verify CSV was attempted from correct path
        mock_data_source.read_csv.assert_called_once_with(
            "test/results/Audi_RS7_Sportback_Symmetric_Morph_101/export_force_series.csv"
        )
        
        # Verify results contain expected fields
        assert result is not None
        assert result['simulator'] == "JakubNet"
        assert 'drag_n' in result
        assert 'lift_n' in result
        assert 'cd' in result
        assert 'cl' in result
    
    def test_extract_from_json(self, sample_results_json):
        """Test extracting data from results JSON."""
        extractor = ResultsExtractor(Mock())
        
        result = extractor._extract_from_json(sample_results_json)
        
        # Values from the actual results.json
        assert result['lift_n'] == 48.847592430907355
        assert result['drag_n'] == 170.04170420635143
        assert result['converged'] is True
        assert 'cd' in result
        assert 'cl' in result
        assert result['cd'] is not None
        assert result['cl'] is not None
        # Check parameters are extracted
        assert result['density'] == 1.225
        assert result['velocity'] == 30.0
        assert result['area'] == 1.1131598667087552
    
    def test_calculate_coefficient(self):
        """Test coefficient calculation formula."""
        extractor = ResultsExtractor(Mock())
        
        # C = 2*F / (rho * v^2 * A)
        # With: F=100N, rho=1.225, v=27.78, A=2.5
        # Expected: C = 200 / (1.225 * 27.78^2 * 2.5)
        
        cd = extractor._calculate_coefficient(
            force_n=100.0,
            density=1.225,
            velocity=27.78,
            area=2.5
        )
        
        assert cd is not None
        assert cd > 0
        
        # Verify formula
        expected_c = 2 * 100.0 / (1.225 * 27.78**2 * 2.5)
        assert abs(cd - expected_c) < 1e-6
    
    def test_calculate_coefficient_separate(self):
        """Test calculating drag and lift coefficients separately."""
        extractor = ResultsExtractor(Mock())
        
        cd = extractor._calculate_coefficient(
            force_n=100.0,
            density=1.225,
            velocity=27.78,
            area=2.5
        )
        
        cl = extractor._calculate_coefficient(
            force_n=50.0,
            density=1.225,
            velocity=27.78,
            area=2.5
        )
        
        assert cd is not None
        assert cl is not None
        
        # Verify formula separately
        expected_cd = 2 * 100.0 / (1.225 * 27.78**2 * 2.5)
        expected_cl = 2 * 50.0 / (1.225 * 27.78**2 * 2.5)
        assert abs(cd - expected_cd) < 1e-6
        assert abs(cl - expected_cl) < 1e-6
    
    def test_extract_from_force_series(self, sample_force_series_csv, sample_results_json):
        """Test extracting and averaging from force series CSV."""
        import csv
        extractor = ResultsExtractor(Mock())
        
        # Read the CSV file as list of dicts
        with open(sample_force_series_csv, 'r') as f:
            reader = csv.DictReader(f)
            csv_data = list(reader)
        
        # Extract parameters from results JSON
        parameters = sample_results_json.get('parameters', {})
        
        result = extractor._extract_from_force_series(csv_data, parameters)
        
        assert 'avg_drag_n' in result
        assert 'avg_lift_n' in result
        assert 'std_drag_n' in result
        assert 'std_lift_n' in result
        assert 'avg_cd' in result
        assert 'avg_cl' in result
        
        # Verify values are reasonable (from last 300 iterations of the CSV)
        assert result['avg_cd'] > 0
        assert result['avg_cl'] is not None  # Can be negative or positive
        assert result['avg_drag_n'] > 0
    
    def test_extract_from_force_series_with_custom_signal_length(self):
        """Test averaging with custom signal length."""
        extractor = ResultsExtractor(Mock())
        
        # Create test data as list of dicts (CSV format)
        data = [
            {'Drag Monitor: Drag Monitor (N)': '80', 'Lift Monitor: Lift Monitor (N)': '10'},
            {'Drag Monitor: Drag Monitor (N)': '81', 'Lift Monitor: Lift Monitor (N)': '11'},
            {'Drag Monitor: Drag Monitor (N)': '82', 'Lift Monitor: Lift Monitor (N)': '12'},
            {'Drag Monitor: Drag Monitor (N)': '83', 'Lift Monitor: Lift Monitor (N)': '13'},
            {'Drag Monitor: Drag Monitor (N)': '84', 'Lift Monitor: Lift Monitor (N)': '14'}
        ]
        
        parameters = {
            'Ref_Density[kg/m^3]': 1.225,
            'Ref_Velocity[m/s]': 30.0,
            'A[m^2]': 2.5
        }
        
        # Extract with signal_length=3 (only last 3 values)
        result = extractor._extract_from_force_series(data, parameters, signal_length=3)
        
        # Last 3 drag values: [82, 83, 84] -> avg = 83
        # Last 3 lift values: [12, 13, 14] -> avg = 13
        assert abs(result['avg_drag_n'] - 83.0) < 1e-6
        assert abs(result['avg_lift_n'] - 13.0) < 1e-6
        assert 'avg_cd' in result
        assert 'avg_cl' in result
    
    def test_calculate_coefficient_zero_dynamic_pressure(self):
        """Test that zero dynamic pressure returns None."""
        extractor = ResultsExtractor(Mock())
        
        # Zero area
        c = extractor._calculate_coefficient(
            force_n=100.0,
            density=1.225,
            velocity=27.78,
            area=0.0
        )
        assert c is None
    
    def test_extract_from_json_missing_fields(self):
        """Test handling of missing fields in results JSON."""
        extractor = ResultsExtractor(Mock())
        
        incomplete_json = {
            "results": {
                "Lift_100[N]": 125.5
                # Missing Drag_100[N], Converged_Flag, etc.
            },
            "parameters": {}
        }
        
        result = extractor._extract_from_json(incomplete_json)
        
        # Should handle missing fields gracefully
        assert result.get('lift_n') == 125.5
        assert result.get('drag_n') is None
        assert result.get('converged') is False  # Default when missing
    
    def test_extract_from_json_with_custom_area(self):
        """Test that area from config is used in coefficient calculation."""
        extractor = ResultsExtractor(Mock())
        
        custom_json = {
            "results": {
                "Lift_100[N]": 50.0,
                "Drag_100[N]": 100.0,
                "Converged_Flag": 1.0
            },
            "parameters": {
                "Ref_Density[kg/m^3]": 1.225,
                "Ref_Velocity[m/s]": 30.0,
                "A[m^2]": 2.5  # Custom area from config
            }
        }
        
        result = extractor._extract_from_json(custom_json)
        
        # Verify area is used
        assert result['area'] == 2.5
        
        # Verify coefficients calculated with custom area
        expected_cd = 2 * 100.0 / (1.225 * 30.0**2 * 2.5)
        expected_cl = 2 * 50.0 / (1.225 * 30.0**2 * 2.5)
        
        assert abs(result['cd'] - expected_cd) < 1e-6
        assert abs(result['cl'] - expected_cl) < 1e-6
    
    def test_extract_from_force_series_with_time_column(self):
        """Test that force series works with Time column instead of Iteration."""
        extractor = ResultsExtractor(Mock())
        
        # Create test data with Time as first column
        data = [
            {'Time': '0.1', 'Drag Monitor: Drag Monitor (N)': '90', 'Lift Monitor: Lift Monitor (N)': '15'},
            {'Time': '0.2', 'Drag Monitor: Drag Monitor (N)': '91', 'Lift Monitor: Lift Monitor (N)': '16'},
            {'Time': '0.3', 'Drag Monitor: Drag Monitor (N)': '92', 'Lift Monitor: Lift Monitor (N)': '17'}
        ]
        
        parameters = {
            'Ref_Density[kg/m^3]': 1.225,
            'Ref_Velocity[m/s]': 30.0,
            'A[m^2]': 2.5
        }
        
        result = extractor._extract_from_force_series(data, parameters)
        
        # Should extract values regardless of time vs iteration column
        assert 'avg_cd' in result
        assert 'avg_cl' in result
        assert result['avg_cd'] > 0
        assert result['avg_cl'] > 0
