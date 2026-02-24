"""Main validation data collector orchestrator."""

import logging
from typing import Optional
from lpm_validation.config import Configuration
from lpm_validation.s3_data_source import S3DataSource
from lpm_validation.metadata_extractor import MetadataExtractor
from lpm_validation.simulation_record import SimulationRecord
from lpm_validation.simulation_record_set import SimulationRecordSet

logger = logging.getLogger(__name__)


class ValidationDataCollector:
    """Orchestrates the validation data collection process."""
    
    def __init__(self, config: Configuration):
        """
        Initialize the validation data collector.
        
        Args:
            config: Configuration instance
        """
        self.config = config
        
        # Initialize S3 data source
        logger.info(f"Initializing S3 data source for bucket: {config.s3_bucket}")
        self.data_source = S3DataSource(bucket=config.s3_bucket, aws_profile=config.aws_profile)
        
        # Initialize metadata extractor
        self.metadata_extractor = MetadataExtractor(self.data_source)
    
    def discover_all(self, car_filter: Optional[str] = None) -> SimulationRecordSet:
        """
        Discover all geometries in the geometry folder structure.
        
        Args:
            car_filter: Optional car name to filter (processes only this car)
            
        Returns:
            SimulationRecordSet instance containing all discovered geometries
        """
        record_set = SimulationRecordSet()
        geometries_prefix = self.config.geometries_prefix
        
        logger.info(f"Starting discovery in {geometries_prefix}")
        
        # List all geometry folders
        geometry_folders = self.data_source.list_folders(geometries_prefix)
        
        logger.info(f"Found {len(geometry_folders)} geometry folders")
        
        for geometry_folder in geometry_folders:
            try:
                record = self._create_simulation_record(geometry_folder)
                if record:
                    # Apply car filter if provided
                    if car_filter is None or record.baseline_id == car_filter:
                        record_set.add(record)
            except Exception as e:
                logger.error(f"Error processing {geometry_folder}: {e}")
                continue
        
        logger.info(f"Discovery complete. Found {len(record_set)} simulations")
        
        return record_set
    
    def _create_simulation_record(self, geometry_folder: str) -> Optional[SimulationRecord]:
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
        
        # Extract car name from baseline_id
        car_name = metadata.get('baseline_id', '')
        car_group = self.config.car_groups.get(car_name, 'unknown')
        
        # Extract geometry name from folder path for use in unique_id fallback
        geometry_name = self.data_source.extract_folder_name(geometry_folder)
        
        # Create simulation record
        record = SimulationRecord(
            unique_id=metadata.get('unique_id', geometry_name),
            baseline_id=metadata.get('baseline_id', ''),
            car_group=car_group,
            morph_type=metadata.get('morph_type'),
            morph_value=metadata.get('morph_value')
        )
        
        logger.debug(f"Created record: {record}")
        
        return record
    
    def execute(self, car_filter: Optional[str] = None, simulator_filter: str = "JakubNet") -> dict:
        """
        Execute the complete validation data collection workflow.
        
        Args:
            car_filter: Optional car name to filter (processes only this car)
            simulator_filter: Simulator name to process (default: "JakubNet")
            
        Returns:
            Dictionary with execution statistics
        """
        logger.info("=" * 80)
        logger.info("STARTING VALIDATION DATA COLLECTION")
        logger.info("=" * 80)
        
        try:
            # PHASE 1: Discovery
            logger.info("")
            logger.info("PHASE 1: GEOMETRY DISCOVERY")
            logger.info("-" * 80)
            
            record_set = self.discover_all(car_filter=car_filter)
            
            logger.info(f"Discovered {len(record_set)} geometries")
            
            if len(record_set) == 0:
                logger.warning("No geometries found. Exiting.")
                return {
                    'status': 'no_geometries',
                    'total_geometries': 0,
                    'with_results': 0,
                    'without_results': 0
                }
            
            # PHASE 2: Results Matching
            logger.info("")
            logger.info("PHASE 2: RESULTS MATCHING")
            logger.info("-" * 80)
            logger.info(f"Processing simulator: {simulator_filter}")
            
            # Match results for each simulation record
            for record in record_set:
                record.find_and_extract_results(
                    self.data_source,
                    self.config.results_prefix,
                    simulator_filter=simulator_filter
                )
            
            with_results = record_set.count_with_results()
            without_results = record_set.count_without_results()
            
            logger.info(f"Results matched: {with_results}/{len(record_set)} geometries have results")
            
            # PHASE 3: Export
            logger.info("")
            logger.info("PHASE 3: DATA EXPORT")
            logger.info("-" * 80)
            
            record_set.to_csv(self.config.output_path, group_by_car=True, simulator=simulator_filter)
            logger.info(f"CSV file(s) exported to: {self.config.output_path}")
            
            # PHASE 4: Summary Report
            logger.info("")
            logger.info("PHASE 4: SUMMARY REPORT GENERATION")
            logger.info("-" * 80)
            
            summary_report = record_set.generate_summary_report()
            record_set.save_summary_report(self.config.output_path)
            
            # Print summary to console
            print("\n" + summary_report)
            
            # Completion
            logger.info("")
            logger.info("=" * 80)
            logger.info("VALIDATION DATA COLLECTION COMPLETE")
            logger.info("=" * 80)
            
            return {
                'status': 'success',
                'total_geometries': len(record_set),
                'with_results': with_results,
                'without_results': without_results,
                'output_path': self.config.output_path
            }
            
        except Exception as e:
            logger.error(f"Error during validation data collection: {e}", exc_info=True)
            raise