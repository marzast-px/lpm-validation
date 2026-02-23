"""Results extractor for simulation output files."""

import logging
import numpy as np
from typing import Optional, Dict, Any
from lpm_validation.s3_data_source import S3DataSource

logger = logging.getLogger(__name__)


class ResultsExtractor:
    """Extracts and processes results data from simulation outputs."""
    
    def __init__(self, data_source: S3DataSource):
        """
        Initialize results extractor.
        
        Args:
            data_source: S3DataSource instance
        """
        self.data_source = data_source
    
    def extract_from_folder(self, results_folder: str, simulator: str = "JakubNet") -> Optional[Dict[str, Any]]:
        """
        Extract all results data from a results folder.
        
        Args:
            results_folder: S3 path to results folder
            simulator: Simulator name (for coefficient calculation)
            
        Returns:
            Dictionary with extracted results or None
        """
        # Look for results JSON
        json_files = self.data_source.list_files(results_folder, extension='.json')
        
        if not json_files:
            logger.warning(f"No JSON files found in {results_folder}")
            return None
        
        # Read the first JSON file
        json_path = json_files[0]
        json_data = self.data_source.read_json(json_path)
        
        if not json_data:
            return None
        
        results = {}
        
        # Extract from JSON
        results.update(self.extract_from_json(json_data))
        
        # Try to extract from force series CSV
        csv_files = self.data_source.list_files(results_folder, extension='.csv')
        force_series_files = [f for f in csv_files if 'force_series' in f or 'export_force_series' in f]
        
        if force_series_files:
            csv_path = force_series_files[0]
            series_data = self.data_source.read_csv(csv_path)
            
            if series_data:
                series_results = self.extract_from_force_series(series_data, json_data.get('parameters', {}))
                results.update(series_results)
        
        results['simulator'] = simulator
        
        return results
    
    def extract_from_json(self, json_data: Dict) -> Dict[str, Any]:
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
        cd, cl = None, None
        if drag_100 is not None and lift_100 is not None:
            cd, cl = self.calculate_coefficients(drag_100, lift_100, density, velocity, area)
        
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
    
    def extract_from_force_series(self, series_data: list, parameters: Dict) -> Dict[str, Any]:
        """
        Extract and process force series data.
        
        Args:
            series_data: List of CSV rows as dictionaries
            parameters: Reference parameters from JSON
            
        Returns:
            Dictionary with averaged and statistical data
        """
        if not series_data:
            return {}
        
        # Get reference parameters
        density = parameters.get('Ref_Density[kg/m^3]', 1.225)
        velocity = parameters.get('Ref_Velocity[m/s]', 30.0)
        area = parameters.get('A[m^2]', 1.0)
        
        # Extract data from last 300 iterations
        n_avg = min(300, len(series_data))
        last_n = series_data[-n_avg:]
        
        # Extract coefficient and force values
        cd_values = []
        cl_values = []
        drag_values = []
        lift_values = []
        
        for row in last_n:
            try:
                # Try different column name patterns
                cd_val = self._extract_value(row, ['Cd Monitor: Cd Monitor', 'Cd', 'cd'])
                cl_val = self._extract_value(row, ['Cl Monitor: Cl Monitor', 'Cl', 'cl'])
                drag_val = self._extract_value(row, ['Drag Monitor: Drag Monitor (N)', 'Drag', 'drag'])
                lift_val = self._extract_value(row, ['Lift Monitor: Lift Monitor (N)', 'Lift', 'lift'])
                
                if cd_val is not None:
                    cd_values.append(float(cd_val))
                if cl_val is not None:
                    cl_values.append(float(cl_val))
                if drag_val is not None:
                    drag_values.append(float(drag_val))
                if lift_val is not None:
                    lift_values.append(float(lift_val))
                    
            except (ValueError, TypeError) as e:
                logger.debug(f"Skipping row due to conversion error: {e}")
                continue
        
        results = {}
        
        # Calculate averages
        if cd_values:
            results['avg_cd'] = np.mean(cd_values)
            results['std_cd'] = np.std(cd_values)
        
        if cl_values:
            results['avg_cl'] = np.mean(cl_values)
            results['std_cl'] = np.std(cl_values)
        
        if drag_values:
            results['avg_drag_n'] = np.mean(drag_values)
            results['std_drag_n'] = np.std(drag_values)
            
            # Calculate Cd from averaged drag if not already available
            if 'avg_cd' not in results:
                cd_from_drag, _ = self.calculate_coefficients(
                    results['avg_drag_n'], 0, density, velocity, area
                )
                results['avg_cd'] = cd_from_drag
        
        if lift_values:
            results['avg_lift_n'] = np.mean(lift_values)
            results['std_lift_n'] = np.std(lift_values)
            
            # Calculate Cl from averaged lift if not already available
            if 'avg_cl' not in results:
                _, cl_from_lift = self.calculate_coefficients(
                    0, results['avg_lift_n'], density, velocity, area
                )
                results['avg_cl'] = cl_from_lift
        
        logger.debug(f"Averaged {n_avg} iterations: avg_cd={results.get('avg_cd')}, avg_cl={results.get('avg_cl')}")
        
        return results
    
    def _extract_value(self, row: Dict, possible_keys: list) -> Optional[float]:
        """
        Extract value from row trying multiple possible keys.
        
        Args:
            row: CSV row dictionary
            possible_keys: List of possible column names
            
        Returns:
            Extracted value or None
        """
        for key in possible_keys:
            if key in row:
                return row[key]
        return None
    
    @staticmethod
    def calculate_coefficients(drag_n: float, lift_n: float, 
                               density: float, velocity: float, area: float) -> tuple:
        """
        Calculate drag and lift coefficients.
        
        Formula: C = 2 * Force / (density * velocity^2 * area)
        
        Args:
            drag_n: Drag force in Newtons
            lift_n: Lift force in Newtons
            density: Air density (kg/m^3)
            velocity: Reference velocity (m/s)
            area: Reference area (m^2)
            
        Returns:
            Tuple of (Cd, Cl)
        """
        dynamic_pressure_area = density * velocity**2 * area
        
        if dynamic_pressure_area == 0:
            return None, None
        
        cd = 2.0 * drag_n / dynamic_pressure_area
        cl = 2.0 * lift_n / dynamic_pressure_area
        
        return cd, cl
