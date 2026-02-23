"""Unit tests for metadata_extractor module."""

import pytest
import json
from unittest.mock import Mock, patch
from lpm_validation.metadata_extractor import MetadataExtractor


class TestMetadataExtractor:
    """Test MetadataExtractor class."""
    
    def test_extract_from_folder_baseline(self, sample_config, sample_geometry_json):
        """Test extracting metadata from baseline geometry."""
        mock_data_source = Mock()
        mock_data_source.read_json.return_value = sample_geometry_json
        
        extractor = MetadataExtractor(sample_config, mock_data_source)
        
        result = extractor.extract_from_folder("test/geometries/Polestar3_baseline_001")
        
        assert result['unique_id'] == "Polestar3_baseline_001"
        assert result['baseline_id'] == "Polestar3_baseline"
        assert result['car_name'] == "Polestar3"
        assert result['morph_type'] is None
        assert result['morph_value'] is None
    
    def test_extract_from_folder_with_morph(self, sample_config, sample_geometry_morph_json):
        """Test extracting metadata from geometry with morph."""
        mock_data_source = Mock()
        mock_data_source.read_json.return_value = sample_geometry_morph_json
        
        extractor = MetadataExtractor(sample_config, mock_data_source)
        
        result = extractor.extract_from_folder("test/geometries/Polestar3_baseline_002_rh10")
        
        assert result['unique_id'] == "Polestar3_baseline_002_rh10"
        assert result['baseline_id'] == "Polestar3_baseline"
        assert result['car_name'] == "Polestar3"
        assert result['morph_type'] == "ride_height"
        assert result['morph_value'] == 10.0
    
    def test_parse_geometry_json_baseline(self, sample_geometry_json):
        """Test parsing baseline geometry JSON."""
        extractor = MetadataExtractor(Mock(), Mock())
        
        result = extractor.parse_geometry_json(sample_geometry_json)
        
        assert result['unique_id'] == "Polestar3_baseline_001"
        assert result['baseline_id'] == "Polestar3_baseline"
        assert result['morph_type'] is None
    
    def test_parse_geometry_json_with_morph(self, sample_geometry_morph_json):
        """Test parsing geometry JSON with morph."""
        extractor = MetadataExtractor(Mock(), Mock())
        
        result = extractor.parse_geometry_json(sample_geometry_morph_json)
        
        assert result['morph_type'] == "ride_height"
        assert result['morph_value'] == 10.0
    
    def test_identify_morph_parameter_baseline(self):
        """Test identifying no morph for baseline."""
        extractor = MetadataExtractor(Mock(), Mock())
        
        morph_params = {"ride_height": 0.0, "front_dam": 0.0}
        morph_type, morph_value = extractor.identify_morph_parameter(morph_params)
        
        assert morph_type is None
        assert morph_value is None
    
    def test_identify_morph_parameter_single_morph(self):
        """Test identifying single non-zero morph."""
        extractor = MetadataExtractor(Mock(), Mock())
        
        morph_params = {"ride_height": 10.0, "front_dam": 0.0}
        morph_type, morph_value = extractor.identify_morph_parameter(morph_params)
        
        assert morph_type == "ride_height"
        assert morph_value == 10.0
    
    def test_identify_morph_parameter_multiple_morphs(self):
        """Test identifying first non-zero morph when multiple exist."""
        extractor = MetadataExtractor(Mock(), Mock())
        
        morph_params = {"ride_height": 10.0, "front_dam": 5.0}
        morph_type, morph_value = extractor.identify_morph_parameter(morph_params)
        
        # Should return first non-zero
        assert morph_type is not None
        assert morph_value != 0.0
    
    def test_extract_car_name_from_unique_id(self, sample_config):
        """Test extracting car name from unique_id."""
        extractor = MetadataExtractor(sample_config, Mock())
        
        car_name = extractor.extract_car_name("Polestar3_baseline_001", "Polestar3_baseline")
        assert car_name == "Polestar3"
        
        car_name = extractor.extract_car_name("EX90_test_123", "EX90_baseline")
        assert car_name == "EX90"
