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
