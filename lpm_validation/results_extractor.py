"""Results extractor for simulation output files."""

import logging
import numpy as np
from typing import Optional, Dict, Any
from lpm_validation.s3_data_source import S3DataSource

logger = logging.getLogger(__name__)

# TODO: Review how to deal with series & link this closer with simulation record

class ResultsExtractor:
    """Extracts and processes results data from simulation outputs."""
    
    def __init__(self, data_source: S3DataSource):
        """
        Initialize results extractor.
        
        Args:
            data_source: S3DataSource instance
        """
        self.data_source = data_source
    
    def extract_simulation_results(self, results_folder: str, simulator: str = "JakubNet", signal_length: int = 300) -> Optional[Dict[str, Any]]:
        """
        Extract all results data from a results folder.
        
        This is the main method to be called by other classes.
        
        Args:
            results_folder: S3 path to results folder
            simulator: Simulator name
            signal_length: Number of entries to average from force series (default: 300)
            
        Returns:
            Dictionary with extracted results or None
        """
        # Read export_scalars.json
        folder_name = results_folder.rstrip('/').split('/')[-1]
        json_path = f"{results_folder.rstrip('/')}/export_scalars.json"
        json_data = self.data_source.read_json(json_path)
        
        if not json_data:
            logger.warning(f"No JSON data found at {json_path}")
            return None
        
        results = {}
        
        # Extract from JSON
        results.update(self._extract_from_json(json_data))
        
        # Try to extract from export_force_series.csv
        csv_path = f"{results_folder.rstrip('/')}/export_force_series.csv"
        series_data = self.data_source.read_csv(csv_path)
        
        if series_data:
            parameters = json_data.get('parameters', {})
            series_results = self._extract_from_force_series(
                series_data, 
                parameters,
                signal_length=signal_length
            )
            results.update(series_results)
        
        results['simulator'] = simulator
        
        return results
    
    def _extract_from_json(self, json_data: Dict) -> Dict[str, Any]:
        """
        Extract results from JSON data.
        
        Args:
            json_data: Parsed results JSON
            
        Returns:
            Dictionary with extracted data
        """
        results_section = json_data.get('results', {})
        parameters = json_data.get('parameters', {})
        
        # Extract convergence flag
        converged = bool(results_section.get('Converged_Flag', 0))
        
        # Extract forces
        lift_100 = results_section.get('Lift_100[N]')
        drag_100 = results_section.get('Drag_100[N]')
        
        # Get reference parameters
        density = parameters.get('Ref_Density[kg/m^3]', 1.225)
        velocity = parameters.get('Ref_Velocity[m/s]', 30.0)
        area = parameters.get('A[m^2]', 1.0)
        
        # Calculate coefficients
        cd = self._calculate_coefficient(drag_100, density, velocity, area) if drag_100 is not None else None
        cl = self._calculate_coefficient(lift_100, density, velocity, area) if lift_100 is not None else None
        
        return {
            'converged': converged,
            'drag_n': drag_100,
            'lift_n': lift_100,
            'cd': cd,
            'cl': cl,
            'density': density,
            'velocity': velocity,
            'area': area
        }
    
    def _extract_from_force_series(self, series_data: list, parameters: Dict, signal_length: int = 300) -> Dict[str, Any]:
        """
        Extract and process force series data.
        
        Args:
            series_data: List of CSV rows as dictionaries
            parameters: Reference parameters from JSON
            signal_length: Number of last entries to extract and average
            
        Returns:
            Dictionary with averaged force values and statistics
        """
        if not series_data:
            return {}
        
        # Get reference parameters for coefficient calculation
        density = parameters.get('Ref_Density[kg/m^3]', 1.225)
        velocity = parameters.get('Ref_Velocity[m/s]', 30.0)
        area = parameters.get('A[m^2]', 1.0)
        
        # Extract data from last n entries
        n_avg = min(signal_length, len(series_data))
        last_n = series_data[-n_avg:]
        
        # Extract drag force values
        drag_values = self._extract_force_from_series(
            last_n, 
            'Drag Monitor: Drag Monitor (N)'
        )
        
        # Extract lift force values
        lift_values = self._extract_force_from_series(
            last_n,
            'Lift Monitor: Lift Monitor (N)'
        )
        
        results = {}
        
        # Calculate drag statistics and coefficient
        if drag_values:
            avg_drag = np.mean(drag_values)
            results['avg_drag_n'] = avg_drag
            results['std_drag_n'] = np.std(drag_values)
            results['avg_cd'] = self._calculate_coefficient(float(avg_drag), density, velocity, area)
        
        # Calculate lift statistics and coefficient
        if lift_values:
            avg_lift = np.mean(lift_values)
            results['avg_lift_n'] = avg_lift
            results['std_lift_n'] = np.std(lift_values)
            results['avg_cl'] = self._calculate_coefficient(float(avg_lift), density, velocity, area)
        
        logger.debug(f"Averaged {n_avg} iterations: avg_cd={results.get('avg_cd')}, avg_cl={results.get('avg_cl')}")
        
        return results
    
    def _extract_force_from_series(self, series_data: list, column_name: str) -> list:
        """
        Extract force values from a specific column in the series data.
        
        Args:
            series_data: List of CSV rows as dictionaries
            column_name: Column name to extract (e.g., 'Drag Monitor: Drag Monitor (N)')
            
        Returns:
            List of force values
        """
        values = []
        for row in series_data:
            try:
                if column_name in row and row[column_name]:
                    values.append(float(row[column_name]))
            except (ValueError, TypeError) as e:
                logger.debug(f"Skipping row due to conversion error: {e}")
                continue
        return values
    
    @staticmethod
    def _calculate_coefficient(force_n: float, density: float, velocity: float, area: float) -> Optional[float]:
        """
        Calculate aerodynamic coefficient from force.
        
        Formula: C = 2 * Force / (density * velocity^2 * area)
        
        Args:
            force_n: Force in Newtons
            density: Air density (kg/m^3)
            velocity: Reference velocity (m/s)
            area: Reference area (m^2)
            
        Returns:
            Coefficient value or None if dynamic pressure is zero
        """
        dynamic_pressure_area = density * velocity**2 * area
        
        if dynamic_pressure_area == 0:
            return None
        
        coefficient = 2.0 * force_n / dynamic_pressure_area
        
        return coefficient
