"""Configuration module for validation data extraction."""

import yaml
from pathlib import Path
from typing import Dict, Optional


class Configuration:
    """Holds all configuration parameters for the extraction process."""
    
    def __init__(
        self,
        s3_bucket: str,
        geometries_prefix: str = "sim-data/validation/geometries",
        results_prefix: str = "sim-data/validation/outputs",
        output_path: str = "./output",
        car_groups: Optional[Dict[str, str]] = None,
        aws_profile: Optional[str] = None,
        output_to_s3: bool = False,
        max_workers: int = 10
    ):
        """
        Initialize configuration.
        
        Args:
            s3_bucket: S3 bucket name containing simulation data
            geometries_prefix: S3 prefix for geometry data
            results_prefix: S3 prefix for results data
            output_path: Local or S3 path for output files
            car_groups: Dictionary mapping car names to groups (sedan, SUV, etc.)
            aws_profile: Optional AWS profile name
            output_to_s3: Whether to save output to S3
            max_workers: Number of workers for concurrent processing
        """
        self.s3_bucket = s3_bucket
        self.geometries_prefix = geometries_prefix.rstrip('/')
        self.results_prefix = results_prefix.rstrip('/')
        self.output_path = output_path
        self.car_groups = car_groups or {}
        self.aws_profile = aws_profile
        self.output_to_s3 = output_to_s3
        self.max_workers = max_workers
        
        self.validate()
    
    def validate(self):
        """Validate configuration parameters."""
        if not self.s3_bucket:
            raise ValueError("s3_bucket is required")
        
        if not self.geometries_prefix:
            raise ValueError("geometries_prefix is required")
        
        if not self.results_prefix:
            raise ValueError("results_prefix is required")
        
        if not self.output_path:
            raise ValueError("output_path is required")
        
        if not isinstance(self.car_groups, dict):
            raise ValueError("car_groups must be a dictionary")
        
        if self.max_workers < 1:
            raise ValueError("max_workers must be at least 1")
    
    @classmethod
    def from_file(cls, config_path: str) -> 'Configuration':
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to YAML configuration file
            
        Returns:
            Configuration instance
        """
        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        
        return cls(**config_dict)
    
    def to_dict(self) -> Dict:
        """Convert configuration to dictionary."""
        return {
            's3_bucket': self.s3_bucket,
            'geometries_prefix': self.geometries_prefix,
            'results_prefix': self.results_prefix,
            'output_path': self.output_path,
            'car_groups': self.car_groups,
            'aws_profile': self.aws_profile,
            'output_to_s3': self.output_to_s3,
            'max_workers': self.max_workers
        }
