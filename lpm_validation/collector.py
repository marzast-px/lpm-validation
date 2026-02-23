"""Main validation data collector orchestrator."""

import logging
from typing import Optional, List
from lpm_validation.config import Configuration
from lpm_validation.s3_data_source import S3DataSource
from lpm_validation.metadata_extractor import MetadataExtractor
from lpm_validation.simulation_record import SimulationRecord
from lpm_validation.results_matcher import ResultsMatcher
from lpm_validation.csv_exporter import CSVExporter
from lpm_validation.summary_report import SummaryReportGenerator

logger = logging.getLogger(__name__)


class ValidationDataCollector:
    """Orchestrates the validation data collection process."""
    
    def __init__(self, config: Configuration, output_to_s3: bool = False):
        """
        Initialize the validation data collector.
        
        Args:
            config: Configuration instance
            output_to_s3: Whether to output to S3 (default: False for local)
        """
        self.config = config
        self.output_to_s3 = output_to_s3
        
        # Initialize S3 data source
        logger.info(f"Initializing S3 data source for bucket: {config.s3_bucket}")
        self.data_source = S3DataSource(bucket=config.s3_bucket, aws_profile=config.aws_profile)
        
        # Initialize metadata extractor
        self.metadata_extractor = MetadataExtractor(self.data_source)
        
        # Initialize components
        self.matcher = ResultsMatcher(
            config=config,
            data_source=self.data_source
        )
        
        self.exporter = CSVExporter(
            output_path=config.output_path,
            data_source=self.data_source if output_to_s3 else None,
            output_to_s3=output_to_s3
        )
        
        self.report_generator = SummaryReportGenerator(
            output_path=config.output_path,
            data_source=self.data_source if output_to_s3 else None,
            output_to_s3=output_to_s3
        )
    
    def discover_all(self, car_filter: Optional[str] = None) -> List[SimulationRecord]:
        """
        Discover all simulations in the geometry folder structure.
        
        Args:
            car_filter: Optional car name to filter (processes only this car)
            
        Returns:
            List of SimulationRecord instances
        """
        simulation_records = []
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
                    if car_filter is None or record.car_name == car_filter:
                        simulation_records.append(record)
            except Exception as e:
                logger.error(f"Error processing {geometry_folder}: {e}")
                continue
        
        logger.info(f"Discovery complete. Found {len(simulation_records)} simulations")
        
        return simulation_records
    
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
        
        # Extract geometry name from folder path
        geometry_name = self.data_source.extract_folder_name(geometry_folder)
        
        # Extract car name from baseline_id by removing _Symmetric suffix
        baseline_id = metadata.get('baseline_id', '')
        if baseline_id:
            car_name = baseline_id.replace('_Symmetric', '')
        else:
            # Fall back to unique_id if no baseline_id
            unique_id = metadata.get('unique_id', '')
            car_name = unique_id.split('_Morph_')[0].replace('_Symmetric', '') if unique_id else 'Unknown'
        
        car_group = self.config.car_groups.get(car_name, 'unknown')
        
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
    
    def execute(self, car_filter: Optional[str] = None) -> dict:
        """
        Execute the complete validation data collection workflow.
        
        Args:
            car_filter: Optional car name to filter (processes only this car)
            
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
            
            simulation_records = self.discover_all(car_filter=car_filter)
            
            logger.info(f"Discovered {len(simulation_records)} geometries")
            
            if len(simulation_records) == 0:
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
            
            simulation_records = self.matcher.match_all(simulation_records)
            
            with_results = sum(1 for r in simulation_records if r.has_results)
            without_results = len(simulation_records) - with_results
            
            logger.info(f"Results matched: {with_results}/{len(simulation_records)} geometries have results")
            
            # PHASE 3: Export
            logger.info("")
            logger.info("PHASE 3: DATA EXPORT")
            logger.info("-" * 80)
            
            self.exporter.export_grouped_by_car(simulation_records)
            
            logger.info(f"CSV files exported to {'S3' if self.output_to_s3 else 'local'}: {self.config.output_path}")
            
            # PHASE 4: Summary Report
            logger.info("")
            logger.info("PHASE 4: SUMMARY REPORT GENERATION")
            logger.info("-" * 80)
            
            summary_report = self.report_generator.generate_validation_summary(simulation_records)
            
            # Print summary to console
            print("\n" + summary_report)
            
            # Completion
            logger.info("")
            logger.info("=" * 80)
            logger.info("VALIDATION DATA COLLECTION COMPLETE")
            logger.info("=" * 80)
            
            return {
                'status': 'success',
                'total_geometries': len(simulation_records),
                'with_results': with_results,
                'without_results': without_results,
                'output_path': self.config.output_path
            }
            
        except Exception as e:
            logger.error(f"Error during validation data collection: {e}", exc_info=True)
            raise