"""Data models for simulation records."""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class SimulationRecord:
    """Data model representing a single simulation."""
    
    # Identification
    car_name: str
    car_group: str
    geometry_name: str
    unique_id: str
    
    # Metadata from geometry JSON
    baseline_id: str
    morph_type: Optional[str] = None
    morph_value: Optional[float] = None
    morph_parameters: Dict[str, float] = field(default_factory=dict)
    
    # S3 path
    s3_path: str = ""
    
    # Results data
    has_results: bool = False
    simulator: Optional[str] = None
    converged: Optional[bool] = None
    
    # Force coefficients
    cd: Optional[float] = None
    cl: Optional[float] = None
    cd_front: Optional[float] = None
    cl_front: Optional[float] = None
    cl_rear: Optional[float] = None
    cs: Optional[float] = None
    
    # Forces
    drag_n: Optional[float] = None
    lift_n: Optional[float] = None
    
    # Averaged forces (from series)
    avg_cd: Optional[float] = None
    avg_cl: Optional[float] = None
    avg_drag_n: Optional[float] = None
    avg_lift_n: Optional[float] = None
    
    # Statistical metrics
    std_cd: Optional[float] = None
    std_cl: Optional[float] = None
    std_drag_n: Optional[float] = None
    std_lift_n: Optional[float] = None
    
    def set_metadata(self, baseline_id: str, morph_type: Optional[str], 
                    morph_value: Optional[float], morph_parameters: Dict[str, float]):
        """Set simulation metadata."""
        self.baseline_id = baseline_id
        self.morph_type = morph_type
        self.morph_value = morph_value
        self.morph_parameters = morph_parameters
    
    def set_results(self, converged: bool, simulator: str, **kwargs):
        """Set results data."""
        self.has_results = True
        self.converged = converged
        self.simulator = simulator
        
        # Update any additional fields
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def is_complete(self) -> bool:
        """Check if all required data has been populated."""
        return (
            self.car_name is not None and
            self.baseline_id is not None and
            self.has_results
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert record to flat dictionary for CSV export."""
        return asdict(self)
    
    def get_status(self) -> str:
        """Get processing status of this record."""
        if not self.has_results:
            return "pending"
        elif self.is_complete():
            if self.converged:
                return "complete"
            else:
                return "complete_not_converged"
        else:
            return "incomplete"
    
    def __repr__(self) -> str:
        """String representation."""
        return f"SimulationRecord({self.car_name}, {self.geometry_name}, status={self.get_status()})"
    
    def find_and_extract_results(self, data_source, results_extractor, results_prefix: str, 
                                 simulator_filter: str = "JakubNet"):
        """
        Find and extract results for this simulation record.
        
        Args:
            data_source: S3DataSource instance
            results_extractor: ResultsExtractor instance
            results_prefix: S3 prefix for results
            simulator_filter: Simulator name to process (default: "JakubNet")
        """
        # Find matching results folder
        results_folder, simulator = self._find_results_folder(data_source, results_prefix, simulator_filter)
        
        if not results_folder:
            logger.debug(f"No results found for {self.unique_id}")
            self.has_results = False
            return
        
        logger.debug(f"Found results for {self.unique_id} in {results_folder}")
        
        # Extract results data
        results = results_extractor.extract_simulation_results(results_folder, simulator)
        
        if not results:
            logger.warning(f"Failed to extract results from {results_folder}")
            self.has_results = False
            return
        
        # Update with results
        self.set_results(
            converged=results.get('converged', False),
            simulator=simulator,
            cd=results.get('cd'),
            cl=results.get('cl'),
            drag_n=results.get('drag_n'),
            lift_n=results.get('lift_n'),
            avg_cd=results.get('avg_cd'),
            avg_cl=results.get('avg_cl'),
            avg_drag_n=results.get('avg_drag_n'),
            avg_lift_n=results.get('avg_lift_n'),
            std_cd=results.get('std_cd'),
            std_cl=results.get('std_cl'),
            std_drag_n=results.get('std_drag_n'),
            std_lift_n=results.get('std_lift_n')
        )
        
        logger.debug(f"Updated record with results: converged={results.get('converged')}")
    
    def _find_results_folder(self, data_source, results_prefix: str, 
                            simulator_filter: str = "JakubNet") -> tuple[Optional[str], str]:
        """
        Find the results folder matching this simulation's unique_id for the specified simulator.
        
        Args:
            data_source: S3DataSource instance
            results_prefix: S3 prefix for results
            simulator_filter: Simulator name to match (default: "JakubNet")
            
        Returns:
            Tuple of (results_folder_path, simulator_name) or (None, "")
            
        Note:
            - JakubNet: Results folder has no prefix (exact match: unique_id)
            - Other simulators: Results folder has prefix (format: SIMULATOR_unique_id)
        """
        # List all folders under results_prefix
        all_folders = data_source.list_folders(results_prefix)
        
        # JakubNet uses exact match (no prefix)
        if simulator_filter == "JakubNet":
            for folder in all_folders:
                folder_name = data_source.extract_folder_name(folder)
                if folder_name == self.unique_id:
                    return folder, "JakubNet"
        else:
            # Other simulators use prefix format: SIMULATOR_unique_id
            expected_folder_name = f"{simulator_filter}_{self.unique_id}"
            for folder in all_folders:
                folder_name = data_source.extract_folder_name(folder)
                if folder_name == expected_folder_name:
                    return folder, simulator_filter
        
        return None, ""
    
    # ========== CSV Export Support ==========
    
    @staticmethod
    def get_csv_columns() -> list[str]:
        """
        Get list of CSV column names for export.
        
        Returns:
            List of column names
        """
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
    
    def to_csv_row(self) -> Dict[str, Any]:
        """
        Convert record to CSV row dictionary with formatted values.
        
        Returns:
            Dictionary with column names as keys and formatted values
        """
        return {
            'Name': self.geometry_name,
            'Unique_ID': self.unique_id,
            'Car_Name': self.car_name,
            'Car_Group': self.car_group,
            'Simulator': self.simulator or '',
            'Baseline_ID': self.baseline_id,
            'Morph_Type': self.morph_type or '',
            'Morph_Value': self.morph_value if self.morph_value is not None else '',
            'Converged': self.converged if self.converged is not None else '',
            'Cd': f"{self.cd:.6f}" if self.cd is not None else '',
            'Cl': f"{self.cl:.6f}" if self.cl is not None else '',
            'Drag_N': f"{self.drag_n:.4f}" if self.drag_n is not None else '',
            'Lift_N': f"{self.lift_n:.4f}" if self.lift_n is not None else '',
            'Avg_Cd': f"{self.avg_cd:.6f}" if self.avg_cd is not None else '',
            'Avg_Cl': f"{self.avg_cl:.6f}" if self.avg_cl is not None else '',
            'Avg_Drag_N': f"{self.avg_drag_n:.4f}" if self.avg_drag_n is not None else '',
            'Avg_Lift_N': f"{self.avg_lift_n:.4f}" if self.avg_lift_n is not None else '',
            'Std_Cd': f"{self.std_cd:.6f}" if self.std_cd is not None else '',
            'Std_Cl': f"{self.std_cl:.6f}" if self.std_cl is not None else '',
            'Std_Drag_N': f"{self.std_drag_n:.4f}" if self.std_drag_n is not None else '',
            'Std_Lift_N': f"{self.std_lift_n:.4f}" if self.std_lift_n is not None else '',
            'Has_Results': self.has_results,
            'Status': self.get_status()
        }
