"""Unit tests for config module."""

import pytest
import json
import tempfile
from pathlib import Path
from lpm_validation.config import Configuration


class TestConfiguration:
    """Test Configuration class."""
    
    def test_init_with_valid_params(self):
        """Test configuration initialization with valid parameters."""
        config = Configuration(
            s3_bucket="test-bucket",
            geometries_prefix="test/geometries",
            results_prefix="test/results",
            output_path="./output",
            car_groups={"Car1": "Car1"}
        )
        
        assert config.s3_bucket == "test-bucket"
        assert config.geometries_prefix == "test/geometries"
        assert config.results_prefix == "test/results"
        assert config.output_path == "./output"
        assert config.car_groups == {"Car1": "Car1"}
    
    def test_init_missing_required_field(self):
        """Test that missing required field raises ValueError."""
        with pytest.raises(ValueError, match="s3_bucket"):
            Configuration(
                s3_bucket=None,
                geometries_prefix="test/geometries",
                results_prefix="test/results",
                output_path="./output",
                car_groups={}
            )
    
    def test_from_dict(self):
        """Test creating configuration from dictionary."""
        data = {
            "s3_bucket": "test-bucket",
            "geometries_prefix": "test/geometries",
            "results_prefix": "test/results",
            "output_path": "./output",
            "car_groups": {"Car1": "Car1"}
        }
        
        config = Configuration.from_dict(data)
        
        assert config.s3_bucket == "test-bucket"
        assert config.car_groups == {"Car1": "Car1"}
    
    def test_from_file_yaml(self, sample_config_file):
        """Test loading configuration from YAML file."""
        config = Configuration.from_file(sample_config_file)
        
        assert config.s3_bucket == "test-bucket"
        assert config.geometries_prefix == "test/geometries"
        assert "Polestar3" in config.car_groups
    
    def test_from_file_json(self, tmp_path):
        """Test loading configuration from JSON file."""
        config_data = {
            "s3_bucket": "json-bucket",
            "geometries_prefix": "json/geometries",
            "results_prefix": "json/results",
            "output_path": "./json_output",
            "car_groups": {"Car1": "Car1"}
        }
        
        config_file = tmp_path / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        config = Configuration.from_file(str(config_file))
        
        assert config.s3_bucket == "json-bucket"
        assert config.geometries_prefix == "json/geometries"
    
    def test_from_file_not_found(self):
        """Test that loading non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            Configuration.from_file("nonexistent.yaml")
    
    def test_get_car_name_from_unique_id(self, sample_config):
        """Test extracting car name from unique_id."""
        car_name = sample_config.get_car_name("Polestar3_baseline_001")
        assert car_name == "Polestar3"
        
        car_name = sample_config.get_car_name("EX90_test_123")
        assert car_name == "EX90"
    
    def test_get_car_name_unknown(self, sample_config):
        """Test that unknown car returns None."""
        car_name = sample_config.get_car_name("UnknownCar_123")
        assert car_name is None
