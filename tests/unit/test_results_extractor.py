"""Unit tests for results_extractor module."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock
from lpm_validation.results_extractor import ResultsExtractor


class TestResultsExtractor:
    """Test ResultsExtractor class."""
    
    def test_extract_from_json(self, sample_results_json):
        """Test extracting data from results JSON."""
        extractor = ResultsExtractor(Mock())
        
        result = extractor.extract_from_json(sample_results_json)
        
        assert result['lift_n'] == 125.5
        assert result['drag_n'] == 85.3
        assert result['converged'] is True
        assert 'cd' in result
        assert 'cl' in result
    
    def test_calculate_coefficients(self):
        """Test coefficient calculation formula."""
        extractor = ResultsExtractor(Mock())
        
        # C = 2*F / (rho * v^2 * A)
        # With: F=100N, rho=1.225, v=27.78, A=2.5
        # Expected: C = 200 / (1.225 * 27.78^2 * 2.5)
        
        coeffs = extractor.calculate_coefficients(
            drag_n=100.0,
            lift_n=50.0,
            density=1.225,
            velocity=27.78,
            area=2.5
        )
        
        assert 'cd' in coeffs
        assert 'cl' in coeffs
        assert coeffs['cd'] > 0
        assert coeffs['cl'] > 0
        
        # Verify formula
        expected_cd = 2 * 100.0 / (1.225 * 27.78**2 * 2.5)
        assert abs(coeffs['cd'] - expected_cd) < 1e-6
    
    def test_extract_from_force_series(self, sample_force_series_csv):
        """Test extracting and averaging from force series CSV."""
        extractor = ResultsExtractor(Mock())
        
        mock_data_source = Mock()
        # Read the actual CSV for testing
        with open(sample_force_series_csv, 'r') as f:
            csv_content = f.read()
        
        result = extractor.extract_from_force_series(csv_content)
        
        assert 'avg_cd' in result
        assert 'avg_cl' in result
        assert 'avg_drag_n' in result
        assert 'avg_lift_n' in result
        assert 'std_cd' in result
        assert 'std_cl' in result
        
        # Verify averages are reasonable
        assert 0.3 < result['avg_cd'] < 0.4
        assert 0.04 < result['avg_cl'] < 0.06
    
    def test_average_last_n_iterations(self):
        """Test averaging last N iterations."""
        extractor = ResultsExtractor(Mock())
        
        # Create test data
        data = {
            'Cd_Monitor': [0.3, 0.31, 0.32, 0.33, 0.34],
            'Cl_Monitor': [0.05, 0.051, 0.052, 0.053, 0.054],
            'Drag_Monitor': [80, 81, 82, 83, 84],
            'Lift_Monitor': [10, 11, 12, 13, 14]
        }
        df = pd.DataFrame(data)
        
        result = extractor.average_last_n_iterations(df, n=3)
        
        # Last 3 values: [0.32, 0.33, 0.34] -> avg = 0.33
        assert abs(result['avg_cd'] - 0.33) < 1e-6
        # Last 3 values: [0.052, 0.053, 0.054] -> avg = 0.053
        assert abs(result['avg_cl'] - 0.053) < 1e-6
    
    def test_calculate_coefficients_zero_area_raises_error(self):
        """Test that zero reference area raises ValueError."""
        extractor = ResultsExtractor(Mock())
        
        with pytest.raises(ValueError, match="Reference area must be positive"):
            extractor.calculate_coefficients(
                drag_n=100.0,
                lift_n=50.0,
                density=1.225,
                velocity=27.78,
                area=0.0
            )
    
    def test_extract_from_json_missing_fields(self):
        """Test handling of missing fields in results JSON."""
        extractor = ResultsExtractor(Mock())
        
        incomplete_json = {
            "Lift_100[N]": 125.5
            # Missing Drag_100[N], Converged_Flag, etc.
        }
        
        result = extractor.extract_from_json(incomplete_json)
        
        # Should handle missing fields gracefully
        assert result.get('lift_n') == 125.5
        assert result.get('drag_n') is None or 'drag_n' not in result
