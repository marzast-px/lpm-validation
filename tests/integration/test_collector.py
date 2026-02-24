"""Integration tests for ValidationDataCollector."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from lpm_validation.config import Configuration
from lpm_validation.collector import ValidationDataCollector
from lpm_validation.simulation_record import SimulationRecord
from lpm_validation.simulation_record_set import SimulationRecordSet


class TestValidationDataCollector:
    """Integration tests for ValidationDataCollector."""
    
    @patch('lpm_validation.collector.S3DataSource')
    def test_initialization(self, mock_s3_class, sample_config):
        """Test collector initialization."""
        collector = ValidationDataCollector(config=sample_config)
        
        assert collector.config == sample_config
        assert collector.data_source is not None
        assert collector.metadata_extractor is not None
    
    @patch('lpm_validation.collector.S3DataSource')
    @patch('lpm_validation.collector.ValidationDataCollector.discover_all')
    def test_execute_jakubnet_polestar3(
        self, mock_discover, mock_s3_class, 
        sample_config, tmp_path
    ):
        """Test execution with JakubNet simulator and Polestar3 car."""
        # Override output path for testing
        sample_config.output_path = str(tmp_path / "output")
        
        # Mock discovery to return sample records in a record set
        record1 = SimulationRecord(
            unique_id="p3_001",
            car_group="Sedan",
            baseline_id="Polestar3",
            has_results=False
        )
        record2 = SimulationRecord(
            unique_id="p3_002",
            car_group="Sedan",
            baseline_id="Polestar3",
            has_results=False
        )
        
        record_set = SimulationRecordSet()
        record_set.add(record1)
        record_set.add(record2)
        mock_discover.return_value = record_set
        
        # Mock find_and_extract_results on the records
        with patch.object(record1, 'find_and_extract_results') as mock_find1, \
             patch.object(record2, 'find_and_extract_results') as mock_find2:
            
            # Setup first record to have results with JakubNet simulator
            def set_results1(*args, **kwargs):
                record1.has_results = True
                record1.cd = 0.34
                record1.cl = 0.05
                record1.simulator = "JakubNet"
                record1.converged = True
            mock_find1.side_effect = set_results1
            mock_find2.side_effect = lambda *args, **kwargs: None  # Second record has no results
            
            # Execute
            collector = ValidationDataCollector(config=sample_config)
            
            result = collector.execute(car_filter="Polestar3")
            
            # Verify result
            assert result['status'] == 'success'
            assert result['total_geometries'] == 2
            assert result['with_results'] == 1
            assert result['without_results'] == 1
            
            # Verify CSV was created with correct naming
            csv_file = Path(sample_config.output_path) / "JakubNet_Polestar3.csv"
            assert csv_file.exists()
            
            # Verify summary report was created
            summary_file = Path(sample_config.output_path) / "validation_summary.txt"
            assert summary_file.exists()
    
    @patch('lpm_validation.collector.S3DataSource')
    @patch('lpm_validation.collector.ValidationDataCollector.discover_all')
    def test_execute_des_bmw_ix(
        self, mock_discover, mock_s3_class, 
        sample_config, tmp_path
    ):
        """Test execution with DES simulator and BMW_IX car."""
        # Override output path for testing
        sample_config.output_path = str(tmp_path / "output")
        
        # Mock discovery to return sample records in a record set
        record1 = SimulationRecord(
            unique_id="bmw_001",
            car_group="BMW_IX",
            baseline_id="bmw_baseline",
            has_results=False
        )
        record2 = SimulationRecord(
            unique_id="bmw_002",
            car_group="BMW_IX",
            baseline_id="bmw_baseline",
            has_results=False
        )
        
        record_set = SimulationRecordSet()
        record_set.add(record1)
        record_set.add(record2)
        mock_discover.return_value = record_set
        
        # Mock find_and_extract_results on the records
        with patch.object(record1, 'find_and_extract_results') as mock_find1, \
             patch.object(record2, 'find_and_extract_results') as mock_find2:
            
            # Setup first record to have results with DES simulator
            def set_results1(*args, **kwargs):
                record1.has_results = True
                record1.cd = 0.28
                record1.cl = 0.03
                record1.simulator = "DES"
                record1.converged = True
            mock_find1.side_effect = set_results1
            mock_find2.side_effect = lambda *args, **kwargs: None  # Second record has no results
            
            # Execute
            collector = ValidationDataCollector(config=sample_config)
            
            result = collector.execute(car_filter="bmw_baseline", simulator_filter="DES")
            
            # Verify result
            assert result['status'] == 'success'
            assert result['total_geometries'] == 2
            assert result['with_results'] == 1
            assert result['without_results'] == 1
            
            # Verify CSV was created with correct naming
            csv_file = Path(sample_config.output_path) / "DES_bmw_baseline.csv"
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
        mock_discover.return_value = SimulationRecordSet()
        
        collector = ValidationDataCollector(config=sample_config)
        
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
        
        record = SimulationRecord(
            unique_id="p3_001",
            car_group="Polestar3",
            baseline_id="p3_baseline",
            has_results=True,
            cd=0.34,
            cl=0.05
        )
        
        record_set = SimulationRecordSet()
        record_set.add(record)
        mock_discover.return_value = record_set
        
        collector = ValidationDataCollector(config=sample_config)
        
        result = collector.execute(car_filter="Polestar3")
        
        # Verify car_filter was passed to discovery
        mock_discover.assert_called_once_with(car_filter="Polestar3")
    