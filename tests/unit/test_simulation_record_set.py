"""Unit tests for SimulationRecordSet."""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from pathlib import Path
from lpm_validation.simulation_record_set import SimulationRecordSet
from lpm_validation.simulation_record import SimulationRecord


@pytest.fixture
def sample_records():
    """Create sample simulation records for testing."""
    records = [
        SimulationRecord(
            car_group="group1",
            unique_id="car_a_geo1",
            baseline_id="baseline1"
        ),
        SimulationRecord(
            car_group="group1",
            unique_id="car_a_geo2",
            baseline_id="baseline1"
        ),
        SimulationRecord(
            car_group="group2",
            unique_id="car_b_geo3",
            baseline_id="baseline2"
        )
    ]
    
    # Set results for some records
    records[0].set_results(
        converged=True,
        simulator="JakubNet",
        cd=0.25,
        cl=0.05,
        drag_n=100.0,
        lift_n=20.0
    )
    
    records[2].set_results(
        converged=False,
        simulator="OpenFOAM",
        cd=0.30,
        cl=0.10
    )
    
    return records


class TestSimulationRecordSet:
    """Test SimulationRecordSet class."""
    
    def test_initialization(self):
        """Test basic initialization."""
        record_set = SimulationRecordSet()
        
        assert len(record_set) == 0
        assert record_set.records == []
    
    def test_add_record(self, sample_records):
        """Test adding individual records."""
        record_set = SimulationRecordSet()
        
        record_set.add(sample_records[0])
        assert len(record_set) == 1
        
        record_set.add(sample_records[1])
        assert len(record_set) == 2
    
    def test_extend_records(self, sample_records):
        """Test adding multiple records at once."""
        record_set = SimulationRecordSet()
        
        record_set.extend(sample_records)
        assert len(record_set) == 3
    
    def test_iteration(self, sample_records):
        """Test iterating over records."""
        record_set = SimulationRecordSet()
        record_set.extend(sample_records)
        
        count = 0
        for record in record_set:
            assert isinstance(record, SimulationRecord)
            count += 1
        
        assert count == 3
    
    def test_indexing(self, sample_records):
        """Test accessing records by index."""
        record_set = SimulationRecordSet()
        record_set.extend(sample_records)
        
        assert record_set[0] == sample_records[0]
        assert record_set[1] == sample_records[1]
        assert record_set[2] == sample_records[2]
    
    def test_group_by_car(self, sample_records):
        """Test grouping records by car name."""
        record_set = SimulationRecordSet()
        record_set.extend(sample_records)
        
        grouped = record_set.group_by_car()
        
        assert len(grouped) == 2
        assert "baseline1" in grouped
        assert "baseline2" in grouped
        
        assert len(grouped["baseline1"]) == 2
        assert len(grouped["baseline2"]) == 1
    
    def test_filter_by(self, sample_records):
        """Test filtering records by criteria."""
        record_set = SimulationRecordSet()
        record_set.extend(sample_records)
        
        filtered = record_set.filter_by(baseline_id="baseline1")
        assert len(filtered) == 2
    
    def test_with_results(self, sample_records):
        """Test filtering records with results."""
        record_set = SimulationRecordSet()
        record_set.extend(sample_records)
        
        with_results = record_set.with_results()
        
        assert len(with_results) == 2  # records[0] and records[2] have results
    
    def test_without_results(self, sample_records):
        """Test filtering records without results."""
        record_set = SimulationRecordSet()
        record_set.extend(sample_records)
        
        without_results = record_set.without_results()
        
        assert len(without_results) == 1  # only records[1] has no results
    
    def test_count_with_results(self, sample_records):
        """Test counting records with results."""
        record_set = SimulationRecordSet()
        record_set.extend(sample_records)
        
        assert record_set.count_with_results() == 2
    
    def test_count_without_results(self, sample_records):
        """Test counting records without results."""
        record_set = SimulationRecordSet()
        record_set.extend(sample_records)
        
        assert record_set.count_without_results() == 1
    
    def test_get_car_statistics(self, sample_records):
        """Test getting car statistics."""
        record_set = SimulationRecordSet()
        record_set.extend(sample_records)
        
        car_stats = record_set.get_car_statistics()
        
        assert "baseline1" in car_stats
        assert car_stats["baseline1"]["total"] == 2
        assert car_stats["baseline1"]["with_results"] == 1
        assert car_stats["baseline1"]["without_results"] == 1
        
        assert "baseline2" in car_stats
        assert car_stats["baseline2"]["total"] == 1
        assert car_stats["baseline2"]["with_results"] == 1
        assert car_stats["baseline2"]["without_results"] == 0
    
    def test_get_simulator_statistics(self, sample_records):
        """Test getting simulator statistics."""
        record_set = SimulationRecordSet()
        record_set.extend(sample_records)
        
        sim_stats = record_set.get_simulator_statistics()
        
        assert "JakubNet" in sim_stats
        assert sim_stats["JakubNet"] == 1
        
        assert "OpenFOAM" in sim_stats
        assert sim_stats["OpenFOAM"] == 1
    
    def test_get_convergence_statistics(self, sample_records):
        """Test getting convergence statistics."""
        record_set = SimulationRecordSet()
        record_set.extend(sample_records)
        
        conv_stats = record_set.get_convergence_statistics()
        
        assert conv_stats["converged"] == 1
        assert conv_stats["not_converged"] == 1
        assert conv_stats["unknown"] == 0
    
    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', create=True)
    def test_to_csv_local_grouped(self, mock_open, mock_mkdir, sample_records):
        """Test CSV export to local file system grouped by car."""
        record_set = SimulationRecordSet()
        record_set.extend(sample_records)
        
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        record_set.to_csv("/tmp/output", group_by_car=True)
        
        # Should create directory
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        
        # Should create 2 files (one per car)
        assert mock_open.call_count == 2
    
    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', create=True)
    def test_to_csv_local_not_grouped(self, mock_open, mock_mkdir, sample_records):
        """Test CSV export to local file system not grouped."""
        record_set = SimulationRecordSet()
        record_set.extend(sample_records)
        
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        record_set.to_csv("/tmp/output", group_by_car=False)
        
        # Should create 1 file
        assert mock_open.call_count == 1
    
    def test_generate_summary_report(self, sample_records):
        """Test summary report generation."""
        record_set = SimulationRecordSet()
        record_set.extend(sample_records)
        
        report = record_set.generate_summary_report()
        
        assert "VALIDATION DATA SUMMARY REPORT" in report
        assert "OVERALL STATISTICS" in report
        assert "Total Geometries:" in report
        assert "RESULTS BY CAR" in report
        assert "baseline1" in report
        assert "baseline2" in report
        assert "RESULTS BY SIMULATOR" in report
        assert "JakubNet" in report
        assert "OpenFOAM" in report
        assert "CONVERGENCE STATUS" in report
    
    @patch('pathlib.Path.mkdir')
    @patch('builtins.open', create=True)
    def test_save_summary_report(self, mock_open, mock_mkdir, sample_records):
        """Test saving summary report to file."""
        record_set = SimulationRecordSet()
        record_set.extend(sample_records)
        
        mock_file = MagicMock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        record_set.save_summary_report("/tmp/output")
        
        # Should create directory
        mock_mkdir.assert_called_once()
        
        # Should write file
        mock_open.assert_called_once()
        mock_file.write.assert_called_once()
    
    def test_percentage_helper(self):
        """Test percentage calculation helper."""
        assert SimulationRecordSet._percentage(50, 100) == " 50.0%"
        assert SimulationRecordSet._percentage(0, 100) == "  0.0%"
        assert SimulationRecordSet._percentage(0, 0) == "  0.0%"
        assert SimulationRecordSet._percentage(33, 100) == " 33.0%"
