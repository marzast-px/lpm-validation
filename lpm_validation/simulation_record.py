"""Data models for simulation records."""

from typing import Optional, Dict, Any
from dataclasses import dataclass, field, asdict


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
