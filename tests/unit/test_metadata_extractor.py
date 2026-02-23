"""Unit tests for metadata_extractor module."""

import pytest
import json
from unittest.mock import Mock, patch
from lpm_validation.metadata_extractor import MetadataExtractor


class TestMetadataExtractor:
    """Test MetadataExtractor class."""
    
    def test_extract_from_folder_baseline(self, sample_geometry_json):
        """Test extracting metadata from baseline geometry."""
        mock_data_source = Mock()
        mock_data_source.read_json.return_value = sample_geometry_json
        
        extractor = MetadataExtractor(mock_data_source)
        
        result = extractor.extract_from_folder("test/geometries/Audi_RS7_Sportback_Symmetric_Morph_101")
        
        mock_data_source.read_json.assert_called_once_with(
            "test/geometries/Audi_RS7_Sportback_Symmetric_Morph_101/Audi_RS7_Sportback_Symmetric_Morph_101.json"
        )
        assert result is not None
        assert result['unique_id'] == "Audi_RS7_Sportback_Symmetric_Morph_101"
        assert result['baseline_id'] == "Audi_RS7_Sportback_Symmetric"
        assert result['morph_type'] is None
        assert result['morph_value'] == 0.0
    
    def test_extract_from_folder_with_morph(self, sample_geometry_morph_json):
        """Test extracting metadata from geometry with morph."""
        mock_data_source = Mock()
        mock_data_source.read_json.return_value = sample_geometry_morph_json
        
        extractor = MetadataExtractor(mock_data_source)
        
        result = extractor.extract_from_folder("test/geometries/Audi_RS7_Sportback_Symmetric_Morph_202")
        
        mock_data_source.read_json.assert_called_once_with(
            "test/geometries/Audi_RS7_Sportback_Symmetric_Morph_202/Audi_RS7_Sportback_Symmetric_Morph_202.json"
        )
        assert result is not None
        assert result['unique_id'] == "Audi_RS7_Sportback_Symmetric_Morph_202"
        assert result['baseline_id'] == "Audi_RS7_Sportback_Symmetric"
        assert result['morph_type'] == "Front Overhang"
        assert result['morph_value'] == 10.0
    
    def test_parse_geometry_json_baseline(self, sample_geometry_json):
        """Test parsing baseline geometry JSON."""
        extractor = MetadataExtractor(Mock())
        
        result = extractor.parse_geometry_json(sample_geometry_json)
        
        assert result['unique_id'] == "Audi_RS7_Sportback_Symmetric_Morph_101"
        assert result['baseline_id'] == "Audi_RS7_Sportback_Symmetric"
        assert result['morph_type'] is None
        assert result['morph_value'] == 0.0
    
    def test_parse_geometry_json_with_morph(self, sample_geometry_morph_json):
        """Test parsing geometry JSON with morph."""
        extractor = MetadataExtractor(Mock())
        
        result = extractor.parse_geometry_json(sample_geometry_morph_json)
        
        assert result['morph_type'] == "Front Overhang"
        assert result['morph_value'] == 10.0
    
    def test_identify_morph_parameter_baseline(self):
        """Test identifying no morph for baseline."""
        extractor = MetadataExtractor(Mock())
        
        morph_params = {
            "Front Fascia Curvature": 0.0,
            "Front Overhang": 0.0,
            "Rear Overhang": 0.0
        }
        morph_type, morph_value = extractor._extract_morph_info(morph_params)
        
        assert morph_type is None
        assert morph_value == 0.0
    
    def test_identify_morph_parameter_single_morph(self):
        """Test identifying single non-zero morph."""
        extractor = MetadataExtractor(Mock())
        
        morph_params = {
            "Front Fascia Curvature": 0.0,
            "Front Overhang": 15.0,
            "Rear Overhang": 0.0
        }
        morph_type, morph_value = extractor._extract_morph_info(morph_params)
        
        assert morph_type == "Front Overhang"
        assert morph_value == 15.0
    
    def test_identify_morph_parameter_multiple_morphs(self):
        """Test identifying first non-zero morph when multiple exist."""
        extractor = MetadataExtractor(Mock())
        
        morph_params = {
            "Front Fascia Curvature": 5.0,
            "Front Overhang": 10.0,
            "Rear Overhang": 0.0
        }
        morph_type, morph_value = extractor._extract_morph_info(morph_params)
        
        # Should return first non-zero
        assert morph_type is not None
        assert morph_value != 0.0
