"""Collection of simulation records with export and reporting capabilities."""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Iterator, Optional
from dataclasses import dataclass, field
from lpm_validation.simulation_record import SimulationRecord

logger = logging.getLogger(__name__)


@dataclass
class SimulationRecordSet:
    """
    Collection of simulation records with built-in export and summary capabilities.
    
    Tightly coupled with SimulationRecord - manages collections of records
    and provides operations on the entire dataset.
    """
    
    records: List[SimulationRecord] = field(default_factory=list)
    
    def __len__(self) -> int:
        """Return number of records in the set."""
        return len(self.records)
    
    def __iter__(self) -> Iterator[SimulationRecord]:
        """Iterate over records."""
        return iter(self.records)
    
    def __getitem__(self, index: int) -> SimulationRecord:
        """Get record by index."""
        return self.records[index]
    
    def add(self, record: SimulationRecord) -> None:
        """
        Add a record to the collection.
        
        Args:
            record: SimulationRecord instance to add
        """
        self.records.append(record)
    
    def extend(self, records: List[SimulationRecord]) -> None:
        """
        Add multiple records to the collection.
        
        Args:
            records: List of SimulationRecord instances
        """
        self.records.extend(records)
    
    # ========== Grouping Operations ==========
    
    def group_by_car(self) -> Dict[str, 'SimulationRecordSet']:
        """
        Group records by car name into separate record sets.
        
        Returns:
            Dictionary mapping car names to SimulationRecordSet instances
        """
        grouped: Dict[str, SimulationRecordSet] = {}
        
        for record in self.records:
            car_name = record.baseline_id
            if car_name not in grouped:
                grouped[car_name] = SimulationRecordSet()
            grouped[car_name].add(record)
        
        return grouped
    
    def filter_by(self, **criteria) -> 'SimulationRecordSet':
        """
        Filter records by criteria.
        
        Args:
            **criteria: Attribute name and value pairs to filter by
            
        Returns:
            New SimulationRecordSet with filtered records
        """
        filtered = SimulationRecordSet()
        
        for record in self.records:
            matches = all(
                getattr(record, attr, None) == value 
                for attr, value in criteria.items()
            )
            if matches:
                filtered.add(record)
        
        return filtered
    
    def with_results(self) -> 'SimulationRecordSet':
        """Get subset of records that have results."""
        return self.filter_by(has_results=True)
    
    def without_results(self) -> 'SimulationRecordSet':
        """Get subset of records that don't have results."""
        return self.filter_by(has_results=False)
    
    # ========== Statistics ==========
    
    def count_with_results(self) -> int:
        """Count records that have results."""
        return sum(1 for r in self.records if r.has_results)
    
    def count_without_results(self) -> int:
        """Count records that don't have results."""
        return len(self.records) - self.count_with_results()
    
    def get_car_statistics(self) -> Dict[str, Dict[str, int]]:
        """
        Calculate statistics grouped by car.
        
        Returns:
            Dictionary mapping car names to statistics dictionaries
        """
        car_stats: Dict[str, Dict[str, int]] = {}
        
        for record in self.records:
            car_name = record.baseline_id
            
            if car_name not in car_stats:
                car_stats[car_name] = {
                    'total': 0,
                    'with_results': 0,
                    'without_results': 0
                }
            
            car_stats[car_name]['total'] += 1
            if record.has_results:
                car_stats[car_name]['with_results'] += 1
            else:
                car_stats[car_name]['without_results'] += 1
        
        return car_stats
    
    def get_simulator_statistics(self) -> Dict[str, int]:
        """
        Calculate statistics grouped by simulator.
        
        Returns:
            Dictionary mapping simulator names to counts
        """
        simulator_stats: Dict[str, int] = {}
        
        for record in self.records:
            if record.has_results and record.simulator:
                simulator = record.simulator
                simulator_stats[simulator] = simulator_stats.get(simulator, 0) + 1
        
        return simulator_stats
    
    def get_convergence_statistics(self) -> Dict[str, int]:
        """
        Calculate convergence statistics.
        
        Returns:
            Dictionary with convergence counts
        """
        stats = {
            'converged': 0,
            'not_converged': 0,
            'unknown': 0
        }
        
        for record in self.records:
            if record.has_results:
                if record.converged is True:
                    stats['converged'] += 1
                elif record.converged is False:
                    stats['not_converged'] += 1
                else:
                    stats['unknown'] += 1
        
        return stats
    
    # ========== CSV Export ==========
    
    def to_csv(self, output_path: str, group_by_car: bool = True, simulator: str = "JakubNet") -> None:
        """
        Export records to CSV file(s) locally.
        
        Args:
            output_path: Directory path for output files
            group_by_car: Whether to create separate files per car (default: True)
            simulator: Simulator name for filename (default: 'JakubNet')
        """
        # Create output directory
        Path(output_path).mkdir(parents=True, exist_ok=True)
        
        if group_by_car:
            grouped = self.group_by_car()
            logger.info(f"Exporting data for {len(grouped)} cars to {output_path}")
            
            for car_name, record_set in grouped.items():
                filename = f"{simulator}_{car_name}.csv"
                filepath = Path(output_path) / filename
                record_set._write_csv_file(filepath)
                logger.info(f"Exported {len(record_set)} records for {car_name}")
        else:
            filename = f"{simulator}_validation_data.csv"
            filepath = Path(output_path) / filename
            self._write_csv_file(filepath)
            logger.info(f"Exported {len(self)} records to {filepath}")
    
    def _write_csv_file(self, filepath: Path) -> None:
        """Write records to local CSV file."""
        columns = SimulationRecord.get_csv_columns()
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            for record in self.records:
                writer.writerow(record.to_csv_row())
        
        logger.debug(f"Wrote CSV to {filepath}")
    
    # ========== Summary Report ==========
    
    def generate_summary_report(self) -> str:
        """
        Generate validation summary report.
        
        Returns:
            Summary report as string
        """
        logger.info("Generating validation summary report")
        
        # Calculate overall stats
        total_geometries = len(self)
        with_results = self.count_with_results()
        without_results = self.count_without_results()
        
        # Get statistics
        car_stats = self.get_car_statistics()
        simulator_stats = self.get_simulator_statistics()
        convergence_stats = self.get_convergence_statistics()
        
        # Build report
        lines = []
        lines.append("=" * 80)
        lines.append("VALIDATION DATA SUMMARY REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Overall statistics
        lines.append("OVERALL STATISTICS")
        lines.append("-" * 80)
        lines.append(f"Total Geometries:          {total_geometries:>6}")
        lines.append(f"With Results:              {with_results:>6} ({self._percentage(with_results, total_geometries)})")
        lines.append(f"Without Results:           {without_results:>6} ({self._percentage(without_results, total_geometries)})")
        lines.append("")
        
        # Car breakdown
        lines.append("RESULTS BY CAR")
        lines.append("-" * 80)
        lines.append(f"{'Car Name':<30} {'Total':>8} {'Available':>10} {'Missing':>10} {'%':>6}")
        lines.append("-" * 80)
        
        for car_name in sorted(car_stats.keys()):
            stats = car_stats[car_name]
            lines.append(
                f"{car_name:<30} "
                f"{stats['total']:>8} "
                f"{stats['with_results']:>10} "
                f"{stats['without_results']:>10} "
                f"{self._percentage(stats['with_results'], stats['total']):>6}"
            )
        
        lines.append("-" * 80)
        lines.append("")
        
        # Simulator breakdown
        if simulator_stats:
            lines.append("RESULTS BY SIMULATOR")
            lines.append("-" * 80)
            lines.append(f"{'Simulator':<30} {'Count':>8}")
            lines.append("-" * 80)
            
            for simulator, count in sorted(simulator_stats.items()):
                lines.append(f"{simulator or 'Unknown':<30} {count:>8}")
            
            lines.append("-" * 80)
            lines.append("")
        
        # Convergence status
        if with_results > 0:
            lines.append("CONVERGENCE STATUS")
            lines.append("-" * 80)
            lines.append(f"Converged:                 {convergence_stats['converged']:>6}")
            lines.append(f"Not Converged:             {convergence_stats['not_converged']:>6}")
            lines.append(f"Unknown:                   {convergence_stats['unknown']:>6}")
            lines.append("")
        
        lines.append("=" * 80)
        
        return "\n".join(lines)
    
    def save_summary_report(self, output_path: str, filename: str = "validation_summary.txt") -> None:
        """
        Generate and save summary report to local file.
        
        Args:
            output_path: Directory path for output
            filename: Output filename (default: validation_summary.txt)
        """
        report = self.generate_summary_report()
        
        Path(output_path).mkdir(parents=True, exist_ok=True)
        filepath = Path(output_path) / filename
        
        with open(filepath, 'w') as f:
            f.write(report)
        
        logger.info(f"Summary report saved to {filepath}")
    
    @staticmethod
    def _percentage(value: int, total: int) -> str:
        """Calculate percentage as formatted string."""
        if total == 0:
            return "  0.0%"
        return f"{100.0 * value / total:5.1f}%"
