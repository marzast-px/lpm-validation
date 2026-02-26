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
    
    def test_execute_jakubnet_polestar3(
        self, sample_config, tmp_path
    ):
        """Test execution with JakubNet simulator and Polestar3 car."""
        # Setup
        sample_config.output_path = str(tmp_path / "output")
        
        # Create 3 sample records: 2 Polestar, 1 BMW_IX
        record1 = SimulationRecord(
            unique_id="polestar_001",
            car_group="Polestar3",
            baseline_id="polestar_baseline",
            has_results=False
        )
        record2 = SimulationRecord(
            unique_id="polestar_002",
            car_group="Polestar3",
            baseline_id="polestar_baseline",
            has_results=False
        )
        record3 = SimulationRecord(
            unique_id="bmw_001",
            car_group="BMW_IX",
            baseline_id="bmw_baseline",
            has_results=False
        )
        
        record_set = SimulationRecordSet()
        record_set.add(record1)
        record_set.add(record2)
        record_set.add(record3)
        
        # Mock S3DataSource first
        with patch('lpm_validation.collector.S3DataSource'):
            # Mock discover_all
            with patch.object(ValidationDataCollector, 'discover_all', return_value=record_set):
                # Instead of mocking find_and_extract_results, mock the methods it calls
                # Mock _find_results_folder to return results paths for first 2 records
                call_count = [0]
                def mock_find_folder(self, *args, **kwargs):
                    call_count[0] += 1
                    # First two records find results, third doesn't  
                    if call_count[0] <= 2:
                        return f"test/results/{self.unique_id}", "JakubNet"
                    else:
                        return None, ""
                
                with patch.object(SimulationRecord, '_find_results_folder', mock_find_folder):
                    # Mock ResultsExtractor.extract_simulation_results to return fake results
                    mock_results = {
                        'converged': True,
                        'cd': 0.34,
                        'cl': 0.05,
                        'drag_n': 100.0,
                        'lift_n': 50.0
                    }
                    with patch('lpm_validation.simulation_record.ResultsExtractor.extract_simulation_results', return_value=mock_results):
                        # Execute - override to use only JakubNet
                        collector = ValidationDataCollector(config=sample_config)
                        result = collector.execute(car_filter="Polestar3", simulator_filter="JakubNet")
            
            # Verify result
            assert result['status'] == 'success'
            assert result['total_geometries'] == 3
            assert 'simulators_processed' in result
            assert 'JakubNet' in result['simulators_processed']
            assert result['simulators_processed']['JakubNet']['with_results'] == 2
            assert result['simulators_processed']['JakubNet']['without_results'] == 1
    
    def test_execute_des_bmw_ix(
        self, sample_config, tmp_path
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
        
        # Mock S3DataSource
        with patch('lpm_validation.collector.S3DataSource'):
            # Mock discover_all
            with patch.object(ValidationDataCollector, 'discover_all', return_value=record_set):
                # Mock _find_results_folder to return results path for first record only
                call_count = [0]
                def mock_find_folder(self, *args, **kwargs):
                    call_count[0] += 1
                    # First record finds results, second doesn't
                    if call_count[0] == 1:
                        return f"test/results/DES_{self.unique_id}", "DES"
                    else:
                        return None, ""
                
                with patch.object(SimulationRecord, '_find_results_folder', mock_find_folder):
                    # Mock ResultsExtractor.extract_simulation_results to return fake results
                    mock_results = {
                        'converged': True,
                        'cd': 0.28,
                        'cl': 0.03,
                        'drag_n': 95.0,
                        'lift_n': 45.0
                    }
                    with patch('lpm_validation.simulation_record.ResultsExtractor.extract_simulation_results', return_value=mock_results):
                        # Execute
                        collector = ValidationDataCollector(config=sample_config)
                        result = collector.execute(car_filter="bmw_baseline", simulator_filter="DES")
            
            # Verify result
            assert result['status'] == 'success'
            assert result['total_geometries'] == 2
            assert 'simulators_processed' in result
            assert 'DES' in result['simulators_processed']
            assert result['simulators_processed']['DES']['with_results'] == 1
            assert result['simulators_processed']['DES']['without_results'] == 1
            
            # Verify CSV was created with correct naming
            csv_file = Path(sample_config.output_path) / "DES_bmw_baseline.csv"
            assert csv_file.exists()
            
            # Verify summary report was created
            summary_file = Path(sample_config.output_path) / "DES_validation_summary.txt"
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
    
    def test_execute_single_file_export(
        self, sample_config, tmp_path
    ):
        """Test execution with single-file CSV export (group_by_car=False)."""
        sample_config.output_path = str(tmp_path / "output")
        
        # Create records from different cars
        record1 = SimulationRecord(
            unique_id="p3_001",
            car_group="Sedan",
            baseline_id="Polestar3",
            has_results=False
        )
        record2 = SimulationRecord(
            unique_id="ex90_001",
            car_group="SUV",
            baseline_id="EX90",
            has_results=False
        )
        
        record_set = SimulationRecordSet()
        record_set.add(record1)
        record_set.add(record2)
        
        # Mock S3DataSource
        with patch('lpm_validation.collector.S3DataSource'):
            # Mock discover_all
            with patch.object(ValidationDataCollector, 'discover_all', return_value=record_set):
                # Mock _find_results_folder to return results for both records
                def mock_find_folder(self, *args, **kwargs):
                    # Both records find results
                    return f"test/results/{self.unique_id}", "JakubNet"
                
                with patch.object(SimulationRecord, '_find_results_folder', mock_find_folder):
                    # Mock ResultsExtractor.extract_simulation_results to return fake results
                    def mock_extract_results(results_folder, simulator):
                        # Return different cd values based on unique_id in folder path
                        if "p3_001" in results_folder:
                            return {
                                'converged': True,
                                'cd': 0.34,
                                'cl': 0.05,
                                'drag_n': 100.0,
                                'lift_n': 50.0
                            }
                        else:
                            return {
                                'converged': True,
                                'cd': 0.28,
                                'cl': 0.03,
                                'drag_n': 95.0,
                                'lift_n': 45.0
                            }
                    
                    with patch('lpm_validation.simulation_record.ResultsExtractor.extract_simulation_results', side_effect=mock_extract_results):
                        # Execute with group_by_car=False (single file mode)
                        collector = ValidationDataCollector(config=sample_config)
                        result = collector.execute(group_by_car=False)
            
            # Verify result
            assert result['status'] == 'success'
            assert result['total_geometries'] == 2
            
            # Verify only one CSV file was created (not per-car)
            csv_file = Path(sample_config.output_path) / "JakubNet_validation_data.csv"
            assert csv_file.exists()
            
            # Verify no per-car files were created
            polestar_csv = Path(sample_config.output_path) / "JakubNet_Polestar3.csv"
            ex90_csv = Path(sample_config.output_path) / "JakubNet_EX90.csv"
            assert not polestar_csv.exists()
            assert not ex90_csv.exists()
    
    @patch('lpm_validation.collector.S3DataSource')
    @patch('lpm_validation.collector.ValidationDataCollector.discover_all')
    def test_execute_comma_separated_simulators(
        self, mock_discover, mock_s3_class, sample_config, tmp_path
    ):
        """Test execution with comma-separated simulator list from CLI."""
        sample_config.output_path = str(tmp_path / "output")
        sample_config.simulators = ['JakubNet']  # Config has only JakubNet
        
        # Create sample records
        record1 = SimulationRecord(
            unique_id="p3_001",
            car_group="Sedan",
            baseline_id="Polestar3",
            has_results=False
        )
        
        record_set = SimulationRecordSet()
        record_set.add(record1)
        mock_discover.return_value = record_set
        
        collector = ValidationDataCollector(config=sample_config)
        
        # Execute with comma-separated simulator list (CLI override)
        result = collector.execute(simulator_filter="JakubNet,DES,StarCCM")
        
        # Verify result structure
        assert result['status'] == 'success'
        assert 'simulators_processed' in result
        assert 'JakubNet' in result['simulators_processed']
        assert 'DES' in result['simulators_processed']
        assert 'StarCCM' in result['simulators_processed']
        assert len(result['simulators_processed']) == 3
        
        # Verify separate summary files were created for each simulator
        jakubnet_summary = Path(sample_config.output_path) / "JakubNet_validation_summary.txt"
        des_summary = Path(sample_config.output_path) / "DES_validation_summary.txt"
        starccm_summary = Path(sample_config.output_path) / "StarCCM_validation_summary.txt"
        assert jakubnet_summary.exists()
        assert des_summary.exists()
        assert starccm_summary.exists()
        
        # Verify separate CSV files were created for each simulator
        jakubnet_csv = Path(sample_config.output_path) / "JakubNet_Polestar3.csv"
        des_csv = Path(sample_config.output_path) / "DES_Polestar3.csv"
        starccm_csv = Path(sample_config.output_path) / "StarCCM_Polestar3.csv"
        assert jakubnet_csv.exists()
        assert des_csv.exists()
        assert starccm_csv.exists()
    
    @patch('lpm_validation.collector.S3DataSource')
    @patch('lpm_validation.collector.ValidationDataCollector.discover_all')
    def test_execute_uses_config_simulators(
        self, mock_discover, mock_s3_class, sample_config, tmp_path
    ):
        """Test execution uses simulators from config when no CLI override."""
        sample_config.output_path = str(tmp_path / "output")
        sample_config.simulators = ['JakubNet', 'DES']
        
        # Create sample records
        record1 = SimulationRecord(
            unique_id="p3_001",
            car_group="Sedan",
            baseline_id="Polestar3",
            has_results=False
        )
        
        record_set = SimulationRecordSet()
        record_set.add(record1)
        mock_discover.return_value = record_set
        
        collector = ValidationDataCollector(config=sample_config)
        
        # Execute without simulator_filter (should use config)
        result = collector.execute()
        
        # Verify result structure
        assert result['status'] == 'success'
        assert 'simulators_processed' in result
        assert 'JakubNet' in result['simulators_processed']
        assert 'DES' in result['simulators_processed']
        assert len(result['simulators_processed']) == 2
        
        # Verify separate summary files were created for each simulator
        jakubnet_summary = Path(sample_config.output_path) / "JakubNet_validation_summary.txt"
        des_summary = Path(sample_config.output_path) / "DES_validation_summary.txt"
        assert jakubnet_summary.exists()
        assert des_summary.exists()
        
        # Verify separate CSV files were created for each simulator
        jakubnet_csv = Path(sample_config.output_path) / "JakubNet_Polestar3.csv"
        des_csv = Path(sample_config.output_path) / "DES_Polestar3.csv"
        assert jakubnet_csv.exists()
        assert des_csv.exists()
    
    @patch('lpm_validation.collector.S3DataSource')
    @patch('lpm_validation.collector.ValidationDataCollector.discover_all')
    def test_execute_multi_simulator_with_single_file(
        self, mock_discover, mock_s3_class, sample_config, tmp_path
    ):
        """Test execution with multiple simulators and single-file export."""
        sample_config.output_path = str(tmp_path / "output")
        
        # Create records from different cars
        record1 = SimulationRecord(
            unique_id="p3_001",
            car_group="Sedan",
            baseline_id="Polestar3",
            has_results=False
        )
        record2 = SimulationRecord(
            unique_id="ex90_001",
            car_group="SUV",
            baseline_id="EX90",
            has_results=False
        )
        
        record_set = SimulationRecordSet()
        record_set.add(record1)
        record_set.add(record2)
        mock_discover.return_value = record_set
        
        collector = ValidationDataCollector(config=sample_config)
        
        # Execute with multiple simulators and single-file mode
        result = collector.execute(simulator_filter="JakubNet,DES", group_by_car=False)
        
        # Verify result structure
        assert result['status'] == 'success'
        assert len(result['simulators_processed']) == 2
        
        # Verify single CSV files were created for each simulator (not per-car)
        jakubnet_csv = Path(sample_config.output_path) / "JakubNet_validation_data.csv"
        des_csv = Path(sample_config.output_path) / "DES_validation_data.csv"
        assert jakubnet_csv.exists()
        assert des_csv.exists()
        
        # Verify no per-car files were created
        jakubnet_p3_csv = Path(sample_config.output_path) / "JakubNet_Polestar3.csv"
        des_ex90_csv = Path(sample_config.output_path) / "DES_EX90.csv"
        assert not jakubnet_p3_csv.exists()
        assert not des_ex90_csv.exists()
    