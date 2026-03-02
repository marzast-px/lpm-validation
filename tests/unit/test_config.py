"""Unit tests for config module."""

import pytest
from pathlib import Path
from typing import Optional
from lpm_validation.config import Configuration


class TestConfiguration:
    """Test Configuration class."""
    
    def test_init_with_valid_params(self):
        """Test configuration initialization with valid parameters."""
        config = Configuration(
            s3_bucket="test-bucket",
            simulators=['JakubNet', 'DES'],
            geometries_prefix="test/geometries",
            results_prefix="test/results",
            output_path="./output",
            car_groups={"Car1": "Car1"}
        )
        
        assert config.s3_bucket == "test-bucket"
        assert config.simulators == ['JakubNet', 'DES']
        assert config.geometries_prefix == "test/geometries"
        assert config.results_prefix == "test/results"
        assert config.output_path == "./output"
        assert config.car_groups == {"Car1": "Car1"}
    
    def test_init_missing_required_field(self):
        """Test that missing required field raises ValueError."""
        with pytest.raises(ValueError, match="s3_bucket"):
            Configuration(
                s3_bucket=None,  # type: ignore[arg-type]
                geometries_prefix="test/geometries",
                results_prefix="test/results",
                output_path="./output",
                car_groups={}
            )
    
    def test_from_file_yaml(self, sample_config_file):
        """Test loading configuration from YAML file."""
        config = Configuration.from_file(sample_config_file)
        
        assert config.s3_bucket == "sim-data"
        assert config.simulators == ['JakubNet', 'DES']
        assert config.geometries_prefix == "validation/geometries"
        assert "Polestar3" in config.car_groups
    
    def test_from_file_not_found(self):
        """Test that loading non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            Configuration.from_file("nonexistent.yaml")
    
    def test_to_dict(self, sample_config):
        """Test converting configuration to dictionary."""
        config_dict = sample_config.to_dict()
        
        assert config_dict["s3_bucket"] == "test-bucket"
        assert config_dict["simulators"] == ['JakubNet', 'DES']
        assert config_dict["geometries_prefix"] == "test/geometries"
        assert config_dict["results_prefix"] == "test/results"
        assert config_dict["output_path"] == "./test_output"
        assert "Polestar3" in config_dict["car_groups"]
    
    def test_validate_invalid_car_groups(self):
        """Test that invalid car_groups type raises ValueError."""
        with pytest.raises(ValueError, match="car_groups must be a dictionary"):
            Configuration(
                s3_bucket="test-bucket",
                geometries_prefix="test/geometries",
                results_prefix="test/results",
                output_path="./output",
                car_groups="invalid"  # type: ignore[arg-type]
            )
    
    def test_validate_invalid_max_workers(self):
        """Test that invalid max_workers raises ValueError."""
        with pytest.raises(ValueError, match="max_workers must be at least 1"):
            Configuration(
                s3_bucket="test-bucket",
                geometries_prefix="test/geometries",
                results_prefix="test/results",
                output_path="./output",
                max_workers=0
            )
    
    def test_validate_empty_simulators(self):
        """Test that empty simulators list raises ValueError."""
        with pytest.raises(ValueError, match="simulators list cannot be empty"):
            Configuration(
                s3_bucket="test-bucket",
                simulators=[],
                geometries_prefix="test/geometries",
                results_prefix="test/results",
                output_path="./output"
            )
    
    def test_validate_invalid_simulators_type(self):
        """Test that invalid simulators type raises ValueError."""
        with pytest.raises(ValueError, match="simulators must be a list"):
            Configuration(
                s3_bucket="test-bucket",
                simulators="JakubNet",  # type: ignore[arg-type]
                geometries_prefix="test/geometries",
                results_prefix="test/results",
                output_path="./output"
            )
    
    def test_validate_invalid_simulator_items(self):
        """Test that non-string simulator items raise ValueError."""
        with pytest.raises(ValueError, match="all simulators must be strings"):
            Configuration(
                s3_bucket="test-bucket",
                simulators=["JakubNet", 123],  # type: ignore[list-item]
                geometries_prefix="test/geometries",
                results_prefix="test/results",
                output_path="./output"
            )
    
    def test_default_simulators(self):
        """Test that default simulators is ['JakubNet'] when not specified."""
        config = Configuration(
            s3_bucket="test-bucket",
            geometries_prefix="test/geometries",
            results_prefix="test/results",
            output_path="./output"
        )
        
        assert config.simulators == ['JakubNet']
