"""Unit tests for summary_report module."""

import pytest
from pathlib import Path
from lpm_validation.summary_report import SummaryReportGenerator
from lpm_validation.simulation_record import SimulationRecord


class TestSummaryReportGenerator:
    """Test SummaryReportGenerator class."""
    
    def test_calculate_car_statistics(self):
        """Test calculating statistics by car."""
        generator = SummaryReportGenerator(output_path="./test", output_to_s3=False)
        
        records = [
            SimulationRecord(
                geometry_name="p3_001", unique_id="p3_001",
                car_name="Polestar3", car_group="Polestar3",
                baseline_id="p3_baseline", has_results=True
            ),
            SimulationRecord(
                geometry_name="p3_002", unique_id="p3_002",
                car_name="Polestar3", car_group="Polestar3",
                baseline_id="p3_baseline", has_results=False
            ),
            SimulationRecord(
                geometry_name="ex90_001", unique_id="ex90_001",
                car_name="EX90", car_group="EX90",
                baseline_id="ex90_baseline", has_results=True
            ),
        ]
        
        stats = generator.calculate_car_statistics(records)
        
        assert "Polestar3" in stats
        assert "EX90" in stats
        assert stats["Polestar3"]["total"] == 2
        assert stats["Polestar3"]["with_results"] == 1
        assert stats["Polestar3"]["without_results"] == 1
        assert stats["EX90"]["total"] == 1
        assert stats["EX90"]["with_results"] == 1
    
    def test_calculate_simulator_statistics(self):
        """Test calculating statistics by simulator."""
        generator = SummaryReportGenerator(output_path="./test", output_to_s3=False)
        
        records = [
            SimulationRecord(
                geometry_name="p3_001", unique_id="p3_001",
                car_name="Polestar3", car_group="Polestar3",
                baseline_id="p3_baseline", has_results=True,
                simulator="JakubNet"
            ),
            SimulationRecord(
                geometry_name="p3_002", unique_id="p3_002",
                car_name="Polestar3", car_group="Polestar3",
                baseline_id="p3_baseline", has_results=True,
                simulator="DES"
            ),
            SimulationRecord(
                geometry_name="p3_003", unique_id="p3_003",
                car_name="Polestar3", car_group="Polestar3",
                baseline_id="p3_baseline", has_results=True,
                simulator="JakubNet"
            ),
        ]
        
        stats = generator.calculate_simulator_statistics(records)
        
        assert "JakubNet" in stats
        assert "DES" in stats
        assert stats["JakubNet"] == 2
        assert stats["DES"] == 1
    
    def test_calculate_convergence_statistics(self):
        """Test calculating convergence statistics."""
        generator = SummaryReportGenerator(output_path="./test", output_to_s3=False)
        
        records = [
            SimulationRecord(
                geometry_name="p3_001", unique_id="p3_001",
                car_name="Polestar3", car_group="Polestar3",
                baseline_id="p3_baseline", has_results=True,
                converged=True
            ),
            SimulationRecord(
                geometry_name="p3_002", unique_id="p3_002",
                car_name="Polestar3", car_group="Polestar3",
                baseline_id="p3_baseline", has_results=True,
                converged=False
            ),
            SimulationRecord(
                geometry_name="p3_003", unique_id="p3_003",
                car_name="Polestar3", car_group="Polestar3",
                baseline_id="p3_baseline", has_results=True,
                converged=None
            ),
            SimulationRecord(
                geometry_name="p3_004", unique_id="p3_004",
                car_name="Polestar3", car_group="Polestar3",
                baseline_id="p3_baseline", has_results=False
            ),
        ]
        
        stats = generator.calculate_convergence_statistics(records)
        
        assert stats["converged"] == 1
        assert stats["not_converged"] == 1
        assert stats["unknown"] == 1
    
    def test_generate_validation_summary(self, tmp_path):
        """Test generating validation summary report."""
        output_path = str(tmp_path / "output")
        generator = SummaryReportGenerator(output_path=output_path, output_to_s3=False)
        
        records = [
            SimulationRecord(
                geometry_name="p3_001", unique_id="p3_001",
                car_name="Polestar3", car_group="Polestar3",
                baseline_id="p3_baseline", has_results=True,
                simulator="JakubNet", converged=True
            ),
            SimulationRecord(
                geometry_name="p3_002", unique_id="p3_002",
                car_name="Polestar3", car_group="Polestar3",
                baseline_id="p3_baseline", has_results=False
            ),
        ]
        
        report = generator.generate_validation_summary(records)
        
        assert "VALIDATION DATA SUMMARY REPORT" in report
        assert "Polestar3" in report
        assert "Total Geometries:" in report
        assert "With Results:" in report
        
        # Check that file was created
        report_file = Path(output_path) / "validation_summary.txt"
        assert report_file.exists()
    
    def test_percentage_formatting(self):
        """Test percentage formatting."""
        generator = SummaryReportGenerator(output_path="./test", output_to_s3=False)
        
        pct = generator._percentage(50, 100)
        assert "50.0%" in pct
        
        pct = generator._percentage(1, 3)
        assert "33.3%" in pct
        
        pct = generator._percentage(0, 0)
        assert "0.0%" in pct
