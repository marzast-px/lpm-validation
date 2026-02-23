"""Main validation data collector orchestrator."""

import logging
from typing import Optional
from lpm_validation.config import Configuration
from lpm_validation.s3_data_source import S3DataSource
from lpm_validation.discovery import SimulationDiscovery
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
        self.data_source = S3DataSource(bucket_name=config.s3_bucket)
        
        # Initialize components
        self.discovery = SimulationDiscovery(
            config=config,
            data_source=self.data_source
        )
        
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
            
            simulation_records = self.discovery.discover_all(car_filter=car_filter)
            
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
    
    def test_connection(self) -> bool:
        """
        Test S3 connection and configuration.
        
        Returns:
            True if connection is successful
        """
        try:
            logger.info("Testing S3 connection...")
            
            # Test listing geometries prefix
            folders = self.data_source.list_folders(self.config.geometries_prefix, max_results=1)
            
            logger.info(f"✓ Successfully connected to S3 bucket: {self.config.s3_bucket}")
            logger.info(f"✓ Geometries prefix accessible: {self.config.geometries_prefix}")
            
            if folders:
                logger.info(f"✓ Found at least one geometry folder: {folders[0]}")
            else:
                logger.warning(f"⚠ No geometry folders found at: {self.config.geometries_prefix}")
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Connection test failed: {e}")
            return False
