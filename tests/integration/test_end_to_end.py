"""End-to-end integration tests."""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from lpm_validation.config import Configuration
from lpm_validation.collector import ValidationDataCollector


class TestEndToEnd:
    """End-to-end integration tests."""
    
    @patch('lpm_validation.s3_data_source.boto3.client')
    def test_full_workflow_with_mock_s3(
        self, mock_boto_client, sample_config, tmp_path,
        sample_geometry_json, sample_results_json, sample_force_series_csv
    ):
        """Test complete workflow with mocked S3 data."""
        # Override output path
        sample_config.output_path = str(tmp_path / "output")
        
        # Setup mock S3 client
        mock_s3 = MagicMock()
        
        # Mock list_objects_v2 for geometry discovery
        def mock_list_objects(Bucket, Prefix, **kwargs):
            if 'geometries' in Prefix:
                return {
                    'Contents': [
                        {'Key': 'test/geometries/Polestar3_baseline_001/'},
                        {'Key': 'test/geometries/Polestar3_baseline_001/geometry.json'},
                    ],
                    'IsTruncated': False
                }
            elif 'results' in Prefix or 'outputs' in Prefix:
                return {
                    'Contents': [
                        {'Key': 'test/results/Polestar3_baseline_001/'},
                        {'Key': 'test/results/Polestar3_baseline_001/results.json'},
                    ],
                    'IsTruncated': False
                }
            return {'Contents': [], 'IsTruncated': False}
        
        mock_s3.list_objects_v2.side_effect = mock_list_objects
        
        # Mock get_object for reading files
        def mock_get_object(Bucket, Key):
            if 'geometry.json' in Key:
                return {
                    'Body': Mock(read=lambda: json.dumps(sample_geometry_json).encode())
                }
            elif 'results.json' in Key:
                return {
                    'Body': Mock(read=lambda: json.dumps(sample_results_json).encode())
                }
            elif 'Force_Series.csv' in Key:
                with open(sample_force_series_csv, 'r') as f:
                    content = f.read()
                return {
                    'Body': Mock(read=lambda: content.encode())
                }
            raise Exception(f"Unexpected key: {Key}")
        
        mock_s3.get_object.side_effect = mock_get_object
        mock_boto_client.return_value = mock_s3
        
        # Execute workflow
        collector = ValidationDataCollector(
            config=sample_config,
            output_to_s3=False
        )
        
        result = collector.execute()
        
        # Verify success
        assert result['status'] == 'success'
        assert result['total_geometries'] > 0
        
        # Verify outputs exist
        output_dir = Path(sample_config.output_path)
        assert output_dir.exists()
        
        # Check for CSV files
        csv_files = list(output_dir.glob("*.csv"))
        assert len(csv_files) > 0
        
        # Check for summary report
        summary_file = output_dir / "validation_summary.txt"
        assert summary_file.exists()
        
        # Verify summary content
        with open(summary_file, 'r') as f:
            summary_content = f.read()
            assert "VALIDATION DATA SUMMARY REPORT" in summary_content
    
    def test_configuration_validation(self):
        """Test configuration validation."""
        # Missing required field
        with pytest.raises(ValueError):
            Configuration(
                s3_bucket=None,
                geometries_prefix="test",
                results_prefix="test",
                output_path="./output",
                car_groups={}
            )
        
        # Valid configuration
        config = Configuration(
            s3_bucket="test-bucket",
            geometries_prefix="test/geometries",
            results_prefix="test/results",
            output_path="./output",
            car_groups={"Car1": "Car1"}
        )
        
        assert config.s3_bucket == "test-bucket"
    
    def test_load_config_from_file(self, sample_config_file):
        """Test loading configuration from file."""
        config = Configuration.from_file(sample_config_file)
        
        assert config.s3_bucket == "test-bucket"
        assert config.geometries_prefix == "test/geometries"
        assert "Polestar3" in config.car_groups
    
    @patch('lpm_validation.s3_data_source.boto3.client')
    def test_error_handling_s3_access_denied(self, mock_boto_client, sample_config):
        """Test handling of S3 access denied errors."""
        from botocore.exceptions import ClientError
        
        mock_s3 = MagicMock()
        mock_s3.list_objects_v2.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}},
            'ListObjectsV2'
        )
        mock_boto_client.return_value = mock_s3
        
        collector = ValidationDataCollector(
            config=sample_config,
            output_to_s3=False
        )
        
        # Should handle error gracefully
        with pytest.raises(Exception):
            collector.execute()
