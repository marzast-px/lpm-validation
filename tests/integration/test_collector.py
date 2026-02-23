"""Integration tests for ValidationDataCollector."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from lpm_validation.config import Configuration
from lpm_validation.collector import ValidationDataCollector
from lpm_validation.simulation_record import SimulationRecord


class TestValidationDataCollector:
    """Integration tests for ValidationDataCollector."""
    
    @patch('lpm_validation.collector.S3DataSource')
    def test_initialization(self, mock_s3_class, sample_config):
        """Test collector initialization."""
        collector = ValidationDataCollector(
            config=sample_config,
            output_to_s3=False
        )
        
        assert collector.config == sample_config
        assert collector.output_to_s3 is False
        assert collector.discovery is not None
        assert collector.matcher is not None
        assert collector.exporter is not None
        assert collector.report_generator is not None
    
    @patch('lpm_validation.collector.S3DataSource')
    @patch('lpm_validation.discovery.SimulationDiscovery.discover_all')
    @patch('lpm_validation.results_matcher.ResultsMatcher.match_all')
    def test_execute_success(
        self, mock_match, mock_discover, mock_s3_class, 
        sample_config, tmp_path
    ):
        """Test successful execution workflow."""
        # Override output path for testing
        sample_config.output_path = str(tmp_path / "output")
        
        # Mock discovery to return sample records
        mock_records = [
            SimulationRecord(
                geometry_name="p3_001", unique_id="p3_001",
                car_name="Polestar3", car_group="Polestar3",
                baseline_id="p3_baseline", has_results=False
            ),
            SimulationRecord(
                geometry_name="p3_002", unique_id="p3_002",
                car_name="Polestar3", car_group="Polestar3",
                baseline_id="p3_baseline", has_results=False
            ),
        ]
        mock_discover.return_value = mock_records
        
        # Mock matcher to mark records as having results
        matched_records = [
            SimulationRecord(
                geometry_name="p3_001", unique_id="p3_001",
                car_name="Polestar3", car_group="Polestar3",
                baseline_id="p3_baseline", has_results=True,
                cd=0.34, cl=0.05, simulator="JakubNet",
                converged=True
            ),
            SimulationRecord(
                geometry_name="p3_002", unique_id="p3_002",
                car_name="Polestar3", car_group="Polestar3",
                baseline_id="p3_baseline", has_results=False
            ),
        ]
        mock_match.return_value = matched_records
        
        # Execute
        collector = ValidationDataCollector(
            config=sample_config,
            output_to_s3=False
        )
        
        result = collector.execute()
        
        # Verify result
        assert result['status'] == 'success'
        assert result['total_geometries'] == 2
        assert result['with_results'] == 1
        assert result['without_results'] == 1
        
        # Verify CSV was created
        csv_file = Path(sample_config.output_path) / "Polestar3_validation_data.csv"
        assert csv_file.exists()
        
        # Verify summary report was created
        summary_file = Path(sample_config.output_path) / "validation_summary.txt"
        assert summary_file.exists()
    
    @patch('lpm_validation.collector.S3DataSource')
    @patch('lpm_validation.discovery.SimulationDiscovery.discover_all')
    def test_execute_no_geometries(
        self, mock_discover, mock_s3_class, sample_config
    ):
        """Test execution when no geometries are found."""
        mock_discover.return_value = []
        
        collector = ValidationDataCollector(
            config=sample_config,
            output_to_s3=False
        )
        
        result = collector.execute()
        
        assert result['status'] == 'no_geometries'
        assert result['total_geometries'] == 0
    
    @patch('lpm_validation.collector.S3DataSource')
    @patch('lpm_validation.discovery.SimulationDiscovery.discover_all')
    def test_execute_with_car_filter(
        self, mock_discover, mock_s3_class, sample_config, tmp_path
    ):
        """Test execution with car filter."""
        sample_config.output_path = str(tmp_path / "output")
        
        mock_records = [
            SimulationRecord(
                geometry_name="p3_001", unique_id="p3_001",
                car_name="Polestar3", car_group="Polestar3",
                baseline_id="p3_baseline", has_results=True,
                cd=0.34, cl=0.05
            ),
        ]
        mock_discover.return_value = mock_records
        
        collector = ValidationDataCollector(
            config=sample_config,
            output_to_s3=False
        )
        
        result = collector.execute(car_filter="Polestar3")
        
        # Verify car_filter was passed to discovery
        mock_discover.assert_called_once_with(car_filter="Polestar3")
    
    @patch('lpm_validation.s3_data_source.boto3.client')
    def test_test_connection_success(self, mock_boto_client, sample_config):
        """Test connection test with success."""
        # Setup mock S3 client
        mock_s3 = MagicMock()
        mock_s3.list_objects_v2.return_value = {
            'Contents': [{'Key': 'test/geometries/folder1/'}],
            'IsTruncated': False
        }
        mock_boto_client.return_value = mock_s3
        
        collector = ValidationDataCollector(
            config=sample_config,
            output_to_s3=False
        )
        
        success = collector.test_connection()
        
        assert success is True
    
    @patch('lpm_validation.s3_data_source.boto3.client')
    def test_test_connection_failure(self, mock_boto_client, sample_config):
        """Test connection test with failure."""
        # Setup mock S3 client to raise exception
        mock_s3 = MagicMock()
        mock_s3.list_objects_v2.side_effect = Exception("Connection failed")
        mock_boto_client.return_value = mock_s3
        
        collector = ValidationDataCollector(
            config=sample_config,
            output_to_s3=False
        )
        
        success = collector.test_connection()
        
        assert success is False
