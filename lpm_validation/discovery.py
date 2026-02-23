"""Simulation discovery module."""

import logging
from typing import List, Dict
from lpm_validation.s3_data_source import S3DataSource
from lpm_validation.metadata_extractor import MetadataExtractor
from lpm_validation.simulation_record import SimulationRecord

logger = logging.getLogger(__name__)


class SimulationDiscovery:
    """Discovers all simulations in the geometry folder structure."""
    
    def __init__(self, data_source: S3DataSource, metadata_extractor: MetadataExtractor, 
                 car_groups: Dict[str, str]):
        """
        Initialize simulation discovery.
        
        Args:
            data_source: S3DataSource instance
            metadata_extractor: MetadataExtractor instance
            car_groups: Dictionary mapping car names to groups
        """
        self.data_source = data_source
        self.metadata_extractor = metadata_extractor
        self.car_groups = car_groups
    
    def discover_all(self, geometries_prefix: str) -> List[SimulationRecord]:
        """
        Discover all simulations in the geometry folder structure.
        
        Args:
            geometries_prefix: S3 prefix for geometries
            
        Returns:
            List of SimulationRecord instances
        """
        simulation_records = []
        
        logger.info(f"Starting discovery in {geometries_prefix}")
        
        # List all geometry folders
        geometry_folders = self.data_source.list_folders(geometries_prefix)
        
        logger.info(f"Found {len(geometry_folders)} geometry folders")
        
        for geometry_folder in geometry_folders:
            try:
                record = self.create_simulation_record(geometry_folder)
                if record:
                    simulation_records.append(record)
            except Exception as e:
                logger.error(f"Error processing {geometry_folder}: {e}")
                continue
        
        logger.info(f"Discovery complete. Found {len(simulation_records)} simulations")
        
        return simulation_records
    
    def create_simulation_record(self, geometry_folder: str) -> SimulationRecord:
        """
        Create and populate initial simulation record.
        
        Args:
            geometry_folder: S3 path to geometry folder
            
        Returns:
            SimulationRecord instance or None if error
        """
        # Extract metadata from JSON in folder
        metadata = self.metadata_extractor.extract_from_folder(geometry_folder)
        
        if not metadata:
            logger.warning(f"No metadata found in {geometry_folder}")
            return None
        
        # Extract geometry name from folder path
        geometry_name = self.data_source.extract_folder_name(geometry_folder)
        
        # Get car name and group
        car_name = metadata.get('car_name', 'Unknown')
        car_group = self.car_groups.get(car_name, 'unknown')
        
        # Create simulation record
        record = SimulationRecord(
            car_name=car_name,
            car_group=car_group,
            geometry_name=geometry_name,
            unique_id=metadata.get('unique_id', geometry_name),
            baseline_id=metadata.get('baseline_id', ''),
            morph_type=metadata.get('morph_type'),
            morph_value=metadata.get('morph_value'),
            morph_parameters=metadata.get('morph_parameters', {}),
            s3_path=geometry_folder
        )
        
        logger.debug(f"Created record: {record}")
        
        return record
