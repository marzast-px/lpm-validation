"""CSV exporter module."""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Optional
from lpm_validation.simulation_record import SimulationRecord
from lpm_validation.s3_data_source import S3DataSource

logger = logging.getLogger(__name__)


class CSVExporter:
    """Exports simulation records to CSV files."""
    
    def __init__(self, output_path: str, data_source: Optional[S3DataSource] = None, output_to_s3: bool = False):
        """
        Initialize CSV exporter.
        
        Args:
            output_path: Path for output files
            data_source: Optional S3DataSource for S3 output
            output_to_s3: Whether to output to S3
        """
        self.output_path = output_path
        self.data_source = data_source
        self.output_to_s3 = output_to_s3
        
        # Create output directory if local
        if not output_to_s3:
            Path(output_path).mkdir(parents=True, exist_ok=True)
    
    def export_grouped_by_car(self, simulation_records: List[SimulationRecord]):
        """
        Export simulation records grouped by car.
        
        Args:
            simulation_records: List of SimulationRecord instances
        """
        # Group by car
        grouped = self.group_by_car(simulation_records)
        
        logger.info(f"Exporting data for {len(grouped)} cars")
        
        for car_name, records in grouped.items():
            self.export_car_data(car_name, records)
        
        logger.info("Export complete")
    
    def export_car_data(self, car_name: str, records: List[SimulationRecord]):
        """
        Export data for a single car to CSV.
        
        Args:
            car_name: Name of the car
            records: List of SimulationRecord instances for this car
        """
        filename = f"{car_name}_validation_data.csv"
        
        # Define columns
        columns = self.define_csv_columns()
        
        # Convert records to rows
        rows = []
        for record in records:
            row = self.record_to_row(record, columns)
            rows.append(row)
        
        # Write CSV
        if self.output_to_s3 and self.data_source:
            self.write_to_s3(filename, columns, rows)
        else:
            self.write_to_file(filename, columns, rows)
        
        logger.info(f"Exported {len(rows)} records for {car_name}")
    
    def define_csv_columns(self) -> List[str]:
        """Define the columns for CSV output."""
        return [
            'Name',
            'Unique_ID',
            'Car_Name',
            'Car_Group',
            'Simulator',
            'Baseline_ID',
            'Morph_Type',
            'Morph_Value',
            'Converged',
            'Cd',
            'Cl',
            'Drag_N',
            'Lift_N',
            'Avg_Cd',
            'Avg_Cl',
            'Avg_Drag_N',
            'Avg_Lift_N',
            'Std_Cd',
            'Std_Cl',
            'Std_Drag_N',
            'Std_Lift_N',
            'Has_Results',
            'Status'
        ]
    
    def record_to_row(self, record: SimulationRecord, columns: List[str]) -> Dict:
        """
        Convert SimulationRecord to CSV row.
        
        Args:
            record: SimulationRecord instance
            columns: List of column names
            
        Returns:
            Dictionary representing row
        """
        return {
            'Name': record.geometry_name,
            'Unique_ID': record.unique_id,
            'Car_Name': record.car_name,
            'Car_Group': record.car_group,
            'Simulator': record.simulator or '',
            'Baseline_ID': record.baseline_id,
            'Morph_Type': record.morph_type or '',
            'Morph_Value': record.morph_value if record.morph_value is not None else '',
            'Converged': record.converged if record.converged is not None else '',
            'Cd': f"{record.cd:.6f}" if record.cd is not None else '',
            'Cl': f"{record.cl:.6f}" if record.cl is not None else '',
            'Drag_N': f"{record.drag_n:.4f}" if record.drag_n is not None else '',
            'Lift_N': f"{record.lift_n:.4f}" if record.lift_n is not None else '',
            'Avg_Cd': f"{record.avg_cd:.6f}" if record.avg_cd is not None else '',
            'Avg_Cl': f"{record.avg_cl:.6f}" if record.avg_cl is not None else '',
            'Avg_Drag_N': f"{record.avg_drag_n:.4f}" if record.avg_drag_n is not None else '',
            'Avg_Lift_N': f"{record.avg_lift_n:.4f}" if record.avg_lift_n is not None else '',
            'Std_Cd': f"{record.std_cd:.6f}" if record.std_cd is not None else '',
            'Std_Cl': f"{record.std_cl:.6f}" if record.std_cl is not None else '',
            'Std_Drag_N': f"{record.std_drag_n:.4f}" if record.std_drag_n is not None else '',
            'Std_Lift_N': f"{record.std_lift_n:.4f}" if record.std_lift_n is not None else '',
            'Has_Results': record.has_results,
            'Status': record.get_status()
        }
    
    def group_by_car(self, simulation_records: List[SimulationRecord]) -> Dict[str, List[SimulationRecord]]:
        """
        Group simulation records by car name.
        
        Args:
            simulation_records: List of SimulationRecord instances
            
        Returns:
            Dictionary mapping car names to lists of records
        """
        grouped = {}
        
        for record in simulation_records:
            car_name = record.car_name
            if car_name not in grouped:
                grouped[car_name] = []
            grouped[car_name].append(record)
        
        return grouped
    
    def write_to_file(self, filename: str, columns: List[str], rows: List[Dict]):
        """
        Write CSV to local file.
        
        Args:
            filename: Output filename
            columns: Column names
            rows: List of row dictionaries
        """
        filepath = Path(self.output_path) / filename
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(rows)
        
        logger.debug(f"Wrote CSV to {filepath}")
    
    def write_to_s3(self, filename: str, columns: List[str], rows: List[Dict]):
        """
        Write CSV to S3.
        
        Args:
            filename: Output filename
            columns: Column names
            rows: List of row dictionaries
        """
        import io
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
        
        # Upload to S3
        s3_key = f"{self.output_path.rstrip('/')}/{filename}"
        self.data_source.write_text(s3_key, output.getvalue(), content_type='text/csv')
        
        logger.debug(f"Wrote CSV to S3: {s3_key}")
