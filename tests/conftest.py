"""Pytest configuration and shared fixtures."""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock
from lpm_validation.config import Configuration
from lpm_validation.simulation_record import SimulationRecord


@pytest.fixture
def fixtures_dir():
    """Return path to fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_geometry_json(fixtures_dir):
    """Load sample geometry JSON."""
    with open(fixtures_dir / "geometry.json") as f:
        return json.load(f)


@pytest.fixture
def sample_geometry_morph_json(fixtures_dir):
    """Load sample geometry with morph JSON."""
    with open(fixtures_dir / "geometry_morph.json") as f:
        return json.load(f)


@pytest.fixture
def sample_results_json(fixtures_dir):
    """Load sample results JSON."""
    with open(fixtures_dir / "results.json") as f:
        return json.load(f)


@pytest.fixture
def sample_force_series_csv(fixtures_dir):
    """Return path to sample force series CSV."""
    return str(fixtures_dir / "export_force_series.csv")


@pytest.fixture
def sample_config_file(fixtures_dir):
    """Return path to sample config file."""
    return str(fixtures_dir / "config_test.yaml")


@pytest.fixture
def sample_config():
    """Create sample Configuration object."""
    return Configuration(
        s3_bucket="test-bucket",
        simulators=['JakubNet', 'DES'],
        geometries_prefix="test/geometries",
        results_prefix="test/results",
        output_path="./test_output",
        car_groups={
            "Polestar3": "Sedan",
            "Polestar4": "Sedan",
            "EX90": "SUV"
        }
    )


@pytest.fixture
def sample_simulation_record():
    """Create sample SimulationRecord."""
    return SimulationRecord(
        unique_id="Polestar3_baseline_001",
        car_group="Sedan",
        baseline_id="Polestar3_baseline",
        morph_type=None,
        morph_value=None,
        has_results=False
    )


@pytest.fixture
def sample_simulation_record_with_results():
    """Create sample SimulationRecord with results."""
    return SimulationRecord(
        unique_id="Polestar3_baseline_001",
        car_group="Sedan",
        baseline_id="Polestar3_baseline",
        morph_type=None,
        morph_value=None,
        simulator="JakubNet",
        converged=True,
        cd=0.342,
        cl=0.052,
        drag_n=85.3,
        lift_n=125.5,
        avg_cd=0.3422,
        avg_cl=0.0520,
        avg_drag_n=83.2,
        avg_lift_n=12.5,
        has_results=True
    )


@pytest.fixture
def mock_s3_client():
    """Create mock S3 client."""
    mock_client = MagicMock()
    
    # Mock list_objects_v2 response
    mock_client.list_objects_v2.return_value = {
        'Contents': [
            {'Key': 'test/geometries/Polestar3_baseline_001/'},
            {'Key': 'test/geometries/Polestar3_baseline_002/'},
        ],
        'IsTruncated': False
    }
    
    # Mock get_object response
    mock_client.get_object.return_value = {
        'Body': Mock()
    }
    
    return mock_client


@pytest.fixture
def mock_s3_data_source(mock_s3_client):
    """Create mock S3DataSource."""
    from unittest.mock import patch
    with patch('lpm_validation.s3_data_source.boto3.client', return_value=mock_s3_client):
        from lpm_validation.s3_data_source import S3DataSource
        return S3DataSource(bucket="sim-data")


# Visualization test fixtures

@pytest.fixture
def sample_dataframe():
    """Create sample DataFrame for visualization tests."""
    import pandas as pd
    
    data = {
        'Unique_ID': [
            'Car1_Morph_101', 'Car1_Morph_102', 'Car1_Morph_103',
            'Car2_Morph_101', 'Car2_Morph_102',
        ],
        'Baseline_ID': ['Car1', 'Car1', 'Car1', 'Car2', 'Car2'],
        'Car_Group': ['Sedan', 'Sedan', 'Sedan', 'SUV', 'SUV'],
        'Simulator': ['JakubNet', 'JakubNet', 'DES', 'DES', 'JakubNet'],
        'Morph_Type': [None, 'ride_height', 'ride_height', None, 'front_overhang'],
        'Morph_Value': [0.0, 10.0, 20.0, 0.0, 5.0],
        'Status': ['complete', 'complete', 'complete', 'complete', 'complete'],
        'Has_Results': [True, True, True, True, True],
        'Converged': [True, True, True, True, True],
        'Cd': [0.25, 0.26, 0.27, 0.30, 0.31],
        'Cl': [0.10, 0.11, 0.12, 0.15, 0.16],
        'Drag_N': [100.0, 104.0, 108.0, 120.0, 124.0],
        'Lift_N': [40.0, 44.0, 48.0, 60.0, 64.0],
        'Avg_Cd': [0.250, 0.260, 0.270, 0.300, 0.310],
        'Avg_Cl': [0.100, 0.110, 0.120, 0.150, 0.160],
        'Avg_Drag_N': [100.0, 104.0, 108.0, 120.0, 124.0],
        'Avg_Lift_N': [40.0, 44.0, 48.0, 60.0, 64.0],
    }
    
    return pd.DataFrame(data)


@pytest.fixture
def sample_dataframe_with_morphs():
    """Create sample DataFrame with baseline and morph geometries."""
    import pandas as pd
    
    data = {
        'Unique_ID': [
            'Car1_Morph_101', 'Car1_Morph_102', 'Car1_Morph_103', 'Car1_Morph_104',
            'Car2_Morph_101', 'Car2_Morph_102', 'Car2_Morph_103',
        ],
        'Baseline_ID': ['Car1', 'Car1', 'Car1', 'Car1', 'Car2', 'Car2', 'Car2'],
        'Car_Group': ['Sedan', 'Sedan', 'Sedan', 'Sedan', 'SUV', 'SUV', 'SUV'],
        'Simulator': ['JakubNet', 'JakubNet', 'JakubNet', 'JakubNet', 'DES', 'DES', 'DES'],
        'Morph_Type': [None, 'ride_height', 'ride_height', 'ride_height', None, 'front_overhang', 'front_overhang'],
        'Morph_Value': [0.0, 10.0, 20.0, 30.0, 0.0, 5.0, 10.0],
        'Status': ['complete', 'complete', 'complete', 'complete', 'complete', 'complete', 'complete'],
        'Has_Results': [True, True, True, True, True, True, True],
        'Converged': [True, True, True, True, True, True, True],
        'Cd': [0.25, 0.26, 0.27, 0.28, 0.30, 0.31, 0.32],
        'Cl': [0.10, 0.11, 0.12, 0.13, 0.15, 0.16, 0.17],
        'Drag_N': [100.0, 104.0, 108.0, 112.0, 120.0, 124.0, 128.0],
        'Lift_N': [40.0, 44.0, 48.0, 52.0, 60.0, 64.0, 68.0],
        'Avg_Cd': [0.250, 0.260, 0.270, 0.280, 0.300, 0.310, 0.320],
        'Avg_Cl': [0.100, 0.110, 0.120, 0.130, 0.150, 0.160, 0.170],
        'Avg_Drag_N': [100.0, 104.0, 108.0, 112.0, 120.0, 124.0, 128.0],
        'Avg_Lift_N': [40.0, 44.0, 48.0, 52.0, 60.0, 64.0, 68.0],
    }
    
    return pd.DataFrame(data)


@pytest.fixture
def sample_csv_file(tmp_path, sample_dataframe):
    """Create sample CSV file for testing."""
    csv_path = tmp_path / "test_data.csv"
    sample_dataframe.to_csv(csv_path, index=False)
    return str(csv_path)


@pytest.fixture
def sample_csv_dir(tmp_path, sample_dataframe, sample_dataframe_with_morphs):
    """Create directory with sample CSV files."""
    csv_dir = tmp_path / "csv_data"
    csv_dir.mkdir()
    
    # Create multiple CSV files
    sample_dataframe.to_csv(csv_dir / "jakubnet_results.csv", index=False)
    sample_dataframe_with_morphs.to_csv(csv_dir / "des_results.csv", index=False)
    
    return str(csv_dir)
