"""Unit tests for csv_exporter module."""

import pytest
import csv
from pathlib import Path
from unittest.mock import Mock
from lpm_validation.csv_exporter import CSVExporter
from lpm_validation.simulation_record import SimulationRecord


class TestCSVExporter:
    """Test CSVExporter class."""
    
    def test_init_local_output(self, tmp_path):
        """Test initialization for local output."""
        output_path = str(tmp_path / "output")
        exporter = CSVExporter(output_path=output_path, output_to_s3=False)
        
        assert exporter.output_path == output_path
        assert exporter.output_to_s3 is False
        assert Path(output_path).exists()
    
    def test_group_by_car(self, sample_simulation_record):
        """Test grouping records by car."""
        exporter = CSVExporter(output_path="./test", output_to_s3=False)
        
        records = [
            SimulationRecord(
                geometry_name="p3_001", unique_id="p3_001",
                car_name="Polestar3", car_group="Polestar3",
                baseline_id="p3_baseline"
            ),
            SimulationRecord(
                geometry_name="p3_002", unique_id="p3_002",
                car_name="Polestar3", car_group="Polestar3",
                baseline_id="p3_baseline"
            ),
            SimulationRecord(
                geometry_name="ex90_001", unique_id="ex90_001",
                car_name="EX90", car_group="EX90",
                baseline_id="ex90_baseline"
            ),
        ]
        
        grouped = exporter.group_by_car(records)
        
        assert len(grouped) == 2
        assert "Polestar3" in grouped
        assert "EX90" in grouped
        assert len(grouped["Polestar3"]) == 2
        assert len(grouped["EX90"]) == 1
    
    def test_define_csv_columns(self):
        """Test CSV column definition."""
        exporter = CSVExporter(output_path="./test", output_to_s3=False)
        
        columns = exporter.define_csv_columns()
        
        assert "Name" in columns
        assert "Unique_ID" in columns
        assert "Car_Name" in columns
        assert "Cd" in columns
        assert "Cl" in columns
        assert "Has_Results" in columns
        assert "Status" in columns
    
    def test_record_to_row(self, sample_simulation_record_with_results):
        """Test converting record to CSV row."""
        exporter = CSVExporter(output_path="./test", output_to_s3=False)
        
        columns = exporter.define_csv_columns()
        row = exporter.record_to_row(sample_simulation_record_with_results, columns)
        
        assert row['Car_Name'] == "Polestar3"
        assert row['Simulator'] == "JakubNet"
        assert row['Has_Results'] is True
        assert row['Status'] == "Converged"
        assert "0.342" in str(row['Cd'])
    
    def test_record_to_row_no_results(self, sample_simulation_record):
        """Test converting record without results to CSV row."""
        exporter = CSVExporter(output_path="./test", output_to_s3=False)
        
        columns = exporter.define_csv_columns()
        row = exporter.record_to_row(sample_simulation_record, columns)
        
        assert row['Car_Name'] == "Polestar3"
        assert row['Has_Results'] is False
        assert row['Status'] == "No Results"
        assert row['Cd'] == ''
        assert row['Cl'] == ''
    
    def test_write_to_file(self, tmp_path, sample_simulation_record_with_results):
        """Test writing CSV to local file."""
        output_path = str(tmp_path / "output")
        exporter = CSVExporter(output_path=output_path, output_to_s3=False)
        
        columns = exporter.define_csv_columns()
        rows = [exporter.record_to_row(sample_simulation_record_with_results, columns)]
        
        exporter.write_to_file("test.csv", columns, rows)
        
        csv_file = Path(output_path) / "test.csv"
        assert csv_file.exists()
        
        # Verify CSV content
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            data = list(reader)
            assert len(data) == 1
            assert data[0]['Car_Name'] == "Polestar3"
    
    def test_export_grouped_by_car(self, tmp_path):
        """Test exporting records grouped by car."""
        output_path = str(tmp_path / "output")
        exporter = CSVExporter(output_path=output_path, output_to_s3=False)
        
        records = [
            SimulationRecord(
                geometry_name="p3_001", unique_id="p3_001",
                car_name="Polestar3", car_group="Polestar3",
                baseline_id="p3_baseline", has_results=True,
                cd=0.34, cl=0.05
            ),
            SimulationRecord(
                geometry_name="ex90_001", unique_id="ex90_001",
                car_name="EX90", car_group="EX90",
                baseline_id="ex90_baseline", has_results=True,
                cd=0.32, cl=0.04
            ),
        ]
        
        exporter.export_grouped_by_car(records)
        
        # Check that both CSV files were created
        assert (Path(output_path) / "Polestar3_validation_data.csv").exists()
        assert (Path(output_path) / "EX90_validation_data.csv").exists()
