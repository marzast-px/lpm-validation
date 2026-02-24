"""Summary report generator module."""

import logging
from typing import List, Dict, Optional
from pathlib import Path
from lpm_validation.simulation_record import SimulationRecord
from lpm_validation.s3_data_source import S3DataSource

logger = logging.getLogger(__name__)


class SummaryReportGenerator:
    """Generates summary reports of validation data."""
    
    def __init__(self, output_path: str, data_source: Optional[S3DataSource] = None, output_to_s3: bool = False):
        """
        Initialize summary report generator.
        
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
    
    def generate_validation_summary(self, simulation_records: List[SimulationRecord]) -> str:
        """
        Generate validation summary report.
        
        Args:
            simulation_records: List of SimulationRecord instances
            
        Returns:
            Summary report as string
        """
        logger.info("Generating validation summary report")
        
        # Calculate overall stats
        total_geometries = len(simulation_records)
        with_results = sum(1 for r in simulation_records if r.has_results)
        without_results = total_geometries - with_results
        
        # Group by car
        car_stats = self.calculate_car_statistics(simulation_records)
        
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
        simulator_stats = self.calculate_simulator_statistics(simulation_records)
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
        converged_stats = self.calculate_convergence_statistics(simulation_records)
        if with_results > 0:
            lines.append("CONVERGENCE STATUS")
            lines.append("-" * 80)
            lines.append(f"Converged:                 {converged_stats['converged']:>6}")
            lines.append(f"Not Converged:             {converged_stats['not_converged']:>6}")
            lines.append(f"Unknown:                   {converged_stats['unknown']:>6}")
            lines.append("")
        
        lines.append("=" * 80)
        
        report = "\n".join(lines)
        
        # Save report
        self.save_report(report, "validation_summary.txt")
        
        return report
    
    def calculate_car_statistics(self, simulation_records: List[SimulationRecord]) -> Dict[str, Dict]:
        """
        Calculate statistics grouped by car.
        
        Args:
            simulation_records: List of SimulationRecord instances
            
        Returns:
            Dictionary mapping car names to statistics
        """
        car_stats = {}
        
        for record in simulation_records:
            car_name = record.car_name
            
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
    
    def calculate_simulator_statistics(self, simulation_records: List[SimulationRecord]) -> Dict[str, int]:
        """
        Calculate statistics grouped by simulator.
        
        Args:
            simulation_records: List of SimulationRecord instances
            
        Returns:
            Dictionary mapping simulator names to counts
        """
        simulator_stats = {}
        
        for record in simulation_records:
            if record.has_results and record.simulator:
                simulator = record.simulator
                simulator_stats[simulator] = simulator_stats.get(simulator, 0) + 1
        
        return simulator_stats
    
    def calculate_convergence_statistics(self, simulation_records: List[SimulationRecord]) -> Dict[str, int]:
        """
        Calculate convergence statistics.
        
        Args:
            simulation_records: List of SimulationRecord instances
            
        Returns:
            Dictionary with convergence counts
        """
        stats = {
            'converged': 0,
            'not_converged': 0,
            'unknown': 0
        }
        
        for record in simulation_records:
            if record.has_results:
                if record.converged is True:
                    stats['converged'] += 1
                elif record.converged is False:
                    stats['not_converged'] += 1
                else:
                    stats['unknown'] += 1
        
        return stats
    
    def save_report(self, report: str, filename: str):
        """
        Save report to file or S3.
        
        Args:
            report: Report text
            filename: Output filename
        """
        if self.output_to_s3 and self.data_source:
            s3_key = f"{self.output_path.rstrip('/')}/{filename}"
            self.data_source.write_text(s3_key, report, content_type='text/plain')
            logger.info(f"Summary report saved to S3: {s3_key}")
        else:
            filepath = Path(self.output_path) / filename
            with open(filepath, 'w') as f:
                f.write(report)
            logger.info(f"Summary report saved to {filepath}")
    
    def _percentage(self, value: int, total: int) -> str:
        """Calculate percentage as formatted string."""
        if total == 0:
            return "  0.0%"
        return f"{100.0 * value / total:5.1f}%"
