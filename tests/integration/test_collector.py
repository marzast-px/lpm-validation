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
        assert collector.data_source is not None
        assert collector.metadata_extractor is not None
        assert collector.results_extractor is not None
        assert collector.exporter is not None
        assert collector.report_generator is not None
    
    @patch('lpm_validation.collector.S3DataSource')
    @patch('lpm_validation.collector.ValidationDataCollector.discover_all')
    def test_execute_success(
        self, mock_discover, mock_s3_class, 
        sample_config, tmp_path
    ):
        """Test successful execution workflow."""
        # Override output path for testing
        sample_config.output_path = str(tmp_path / "output")
        
        # Mock discovery to return sample records
        record1 = SimulationRecord(
            geometry_name="p3_001", unique_id="p3_001",
            car_name="Polestar3", car_group="Polestar3",
            baseline_id="p3_baseline", has_results=False,
            s3_path="test/path"
        )
        record2 = SimulationRecord(
            geometry_name="p3_002", unique_id="p3_002",
            car_name="Polestar3", car_group="Polestar3",
            baseline_id="p3_baseline", has_results=False,
            s3_path="test/path"
        )
        mock_records = [record1, record2]
        mock_discover.return_value = mock_records
        
        # Mock find_and_extract_results on the records
        with patch.object(record1, 'find_and_extract_results') as mock_find1, \
             patch.object(record2, 'find_and_extract_results') as mock_find2:
            
            # Setup first record to have results
            def set_results1(*args):
                record1.has_results = True
                record1.cd = 0.34
                record1.cl = 0.05
                record1.simulator = "JakubNet"
                record1.converged = True
            mock_find1.side_effect = set_results1
            mock_find2.side_effect = lambda *args: None  # Second record has no results
            
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
    @patch('lpm_validation.collector.ValidationDataCollector.discover_all')
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
    @patch('lpm_validation.collector.ValidationDataCollector.discover_all')
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
